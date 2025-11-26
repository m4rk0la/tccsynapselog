#from tkinter.font import names
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, send_file, flash
from flask_login import login_required, current_user, login_user, logout_user
from shapely import points
from base.forms import LoginForm
import os
import hashlib
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from data_processing.etl.clientes_etl import processar_etl_clientes, get_estatisticas_usuario
from base.models import LatLong, ClientName, Polygon, OrderHistory, ClientScore, User, db
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# define o blueprint; o Flask vai registrar esse blueprint em create_app()
main = Blueprint('main', __name__, template_folder='templates', static_folder='static', static_url_path='/static')

# ...existing code...
@main.route('/autenticado/grupos', methods=['GET', 'POST', 'DELETE'])
def grupos():
    """
    GET ?action=get  -> retorna clients + areas (JSON)
    POST            -> cria/atualiza áreas a partir de GeoJSON (JSON)
    DELETE          -> deleta área por id (?id=)
    """
    # GET para carregar dados de clientes E áreas salvas
    if request.method == 'GET' and request.args.get('action') == 'get':
        user_id = request.args.get('user_id', None)

        try:
            if user_id:
                try:
                    uid = int(user_id)
                except Exception:
                    uid = user_id
            else:
            # Requer usuário autenticado para mostrar clients/points
                if current_user and getattr(current_user, 'is_authenticated', False):
                    uid = current_user.id
                else:
                # Evita usar 'anon' como filtro e retornar tudo; retorna vazio
                    return jsonify({'success': True, 'clients': [], 'areas': []})
        
            # Debug: confirmar UID utilizado
            print(f"📥 [DEBUG GET] uid processado: {uid} (tipo: {type(uid)})")

            # Busca todos os clientes desse usuário
            clients = ClientName.query.filter_by(user_id=uid).all()
            result = []

            # Busca todos os pontos do usuário e indexa por hash normalizado
            from collections import defaultdict
            latlongs = LatLong.query.filter_by(id_user=uid).all()
            hash_map = defaultdict(list)
            for p in latlongs:
                if not p.hash_client:
                    continue
                key = str(p.hash_client).strip().lower()
                try:
                    lat = float(p.latitude) if p.latitude is not None else None
                    lng = float(p.longitude) if p.longitude is not None else None
                except Exception:
                    lat = p.latitude
                    lng = p.longitude
                hash_map[key].append({
                    'id': p.id,
                    'hash_client': p.hash_client,
                    'latitude': lat,
                    'longitude': lng,
                    'user_point': bool(p.user_point),
                    'id_user': p.id_user
                })

            print(f"📥 [DEBUG GET] Clientes encontrados: {len(clients)} | Pontos latlong (index): {sum(len(v) for v in hash_map.values())}")

            # Monta estrutura por cliente, buscando matching pelo hash normalizado
            for c in clients:
                client_hash_key = str(c.hash_client).strip().lower() if c.hash_client else None
                client_points = hash_map.get(client_hash_key, [])
                result.append({
                    'name_client': c.name_client,
                    'hash_client': c.hash_client,
                    'points': client_points
                })

            # Busca áreas/polígonos salvos do usuário
            areas = []
            try:
                import traceback
                # Busca por uid E também por 'anon' caso o usuário não esteja logado
                if uid == 'anon':
                    polygons = Polygon.query.filter_by(user_id='anon').all()
                else:
                    polygons = Polygon.query.filter_by(user_id=uid).all()

                print(f"📊 [DEBUG GET] Polígonos encontrados: {len(polygons)}")

                for poly in polygons:
                    print(f"  - Polígono ID: {poly.id}, Nome: {poly.group_name}")
                    areas.append({
                        'id': poly.id,
                        'group_name': poly.group_name,
                        'geojson_data': json.loads(poly.geojson_data),
                        'created_at': poly.created_at.isoformat() if poly.created_at else None
                    })
            except Exception as e:
                print(f"❌ [DEBUG GET] Erro ao carregar áreas: {e}")
                import traceback
                traceback.print_exc()

            print(f"✅ [DEBUG GET] Retornando: {len(result)} clientes, {len(areas)} áreas")
            return jsonify({'success': True, 'clients': result, 'areas': areas})
        except Exception as e:
            print(f"❌ [DEBUG GET] Erro geral: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # DELETE para excluir área do banco de dados
    if request.method == 'DELETE':
        try:
            area_id = request.args.get('id')
            user_id = session.get('user_id', 'anon')

            if not area_id:
                return jsonify({'success': False, 'error': 'ID da área não fornecido'}), 400

            # Tenta converter user_id para int
            try:
                uid = int(user_id)
            except Exception:
                uid = user_id

            # Tenta converter area_id para int (correção)
            try:
                area_id_int = int(area_id)
            except Exception:
                area_id_int = area_id

            # Busca e deleta a área (verificando se pertence ao usuário)
            polygon = Polygon.query.filter_by(id=area_id_int, user_id=uid).first()

            if not polygon:
                return jsonify({'success': False, 'error': 'Área não encontrada ou não autorizada'}), 404

            db.session.delete(polygon)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Área excluída com sucesso!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    # POST para salvar novas áreas
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_id = session.get('user_id', 'anon')

            print(f"📥 [DEBUG] Recebendo POST em /grupos")
            print(f"📥 [DEBUG] user_id da sessão: {user_id}")
            print(f"📥 [DEBUG] Dados recebidos: {data}")

            # Tenta converter user_id para int
            try:
                uid = int(user_id)
            except Exception:
                uid = user_id

            if not data or 'features' not in data:
                print(f"❌ [DEBUG] Dados inválidos - data: {data}")
                return jsonify({'success': False, 'error': 'Dados inválidos'})

            # Salva cada feature como um polígono no banco
            saved_count = 0
            updated_count = 0

            for feature in data['features']:
                props = feature.get('properties', {})
                group_name = props.get('name', 'Área sem nome')
                db_id = props.get('db_id')  # ID do banco se já existe

                print(f"💾 [DEBUG] Processando: {group_name} (user_id: {uid}, db_id: {db_id})")

                # Se tem db_id, atualiza ao invés de criar duplicado
                if db_id:
                    polygon = Polygon.query.filter_by(id=db_id, user_id=uid).first()
                    if polygon:
                        polygon.group_name = group_name
                        polygon.geojson_data = json.dumps(feature)
                        updated_count += 1
                        print(f"🔄 [DEBUG] Atualizando área ID {db_id}: {group_name}")
                    else:
                        print(f"⚠️ [DEBUG] Área ID {db_id} não encontrada, criando nova")
                        polygon = Polygon(
                            user_id=uid,
                            group_name=group_name,
                            geojson_data=json.dumps(feature)
                        )
                        db.session.add(polygon)
                        saved_count += 1
                else:
                    # Verifica se já existe área com mesmo nome para evitar duplicação
                    existing = Polygon.query.filter_by(user_id=uid, group_name=group_name).first()
                    if existing:
                        print(f"⚠️ [DEBUG] Área '{group_name}' já existe, atualizando")
                        existing.geojson_data = json.dumps(feature)
                        updated_count += 1
                    else:
                        # Cria nova área
                        polygon = Polygon(
                            user_id=uid,
                            group_name=group_name,
                            geojson_data=json.dumps(feature)
                        )
                        db.session.add(polygon)
                        saved_count += 1

            db.session.commit()

            total_msg = []
            if saved_count > 0:
                total_msg.append(f"{saved_count} área(s) criada(s)")
            if updated_count > 0:
                total_msg.append(f"{updated_count} área(s) atualizada(s)")

            message = ", ".join(total_msg) + " com sucesso!" if total_msg else "Nenhuma alteração necessária"
            print(f"✅ [DEBUG] {message}")

            return jsonify({
                'success': True,
                'message': message,
                'saved': saved_count,
                'updated': updated_count
            })
        except Exception as e:
            db.session.rollback()
            print(f"❌ [DEBUG] Erro ao salvar: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('mapagruposadd.html')


@main.route('/autenticado/painel')
def painel():
    # Calcula estatísticas de clientes por área
    try:
        from ml.geo_utils import GeoUtils
        
        # Obtém o ID do usuário logado
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('main.login'))
        
        # Tenta converter user_id para int
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Busca apenas os clientes do usuário logado (não pontos de base)
        clients = LatLong.query.filter_by(id_user=uid, user_point=False).all()
        clients_data = [{
            'id': c.id, 
            'latitude': c.latitude, 
            'longitude': c.longitude,
            'hash_client': c.hash_client
        } for c in clients]
        
        # Busca apenas os polígonos (áreas) do usuário logado
        polygons = Polygon.query.filter_by(user_id=uid).all()
        polygons_data = []
        
        for p in polygons:
            try:
                geojson = json.loads(p.geojson_data)
                
                # Extrai coordenadas do GeoJSON conforme o formato
                if geojson.get('type') == 'Feature':
                    geometry = geojson.get('geometry', {})
                    if geometry.get('type') == 'Polygon':
                        # GeoJSON Polygon tem coordenadas em [[[lon, lat], ...]]
                        coords_array = geometry.get('coordinates', [[]])[0]
                    elif geometry.get('type') == 'Rectangle':
                        # Retângulo também tem formato similar
                        coords_array = geometry.get('coordinates', [[]])[0]
                    else:
                        print(f"⚠️  Tipo de geometria não suportado: {geometry.get('type')}")
                        continue
                elif geojson.get('type') == 'Polygon':
                    coords_array = geojson.get('coordinates', [[]])[0]
                else:
                    print(f"⚠️  Tipo de GeoJSON não suportado: {geojson.get('type')}")
                    continue
                
                # Converte [lon, lat] para [lat, lon] como esperado pelo GeoUtils
                coords = [[c[1], c[0]] for c in coords_array] if coords_array else []
                
                if len(coords) >= 3:
                    polygons_data.append({
                        'id': p.id,
                        'name': p.group_name,
                        'coordinates': coords
                    })
                else:
                    print(f"⚠️  Área '{p.group_name}' tem menos de 3 coordenadas")
                    
            except Exception as e:
                print(f"❌ Erro ao processar área '{p.group_name}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Filtra clientes por área usando otimização
        if polygons_data:
            result = GeoUtils.filter_clients_by_polygons_optimized(
                clients_data, 
                polygons_data
            )
            
            # Calcula estatísticas
            clients_by_area = {}
            clients_with_area = set()
            
            for polygon in polygons_data:
                poly_id = polygon['id']
                poly_name = polygon['name']
                clients_in_area = result.get(poly_id, [])
                clients_by_area[poly_name] = len(clients_in_area)
                
                # Adiciona IDs ao set de clientes com área
                for client in clients_in_area:
                    clients_with_area.add(client.get('id'))
            
            # Calcula clientes sem área
            total_clients = len(clients_data)
            clients_without_area = total_clients - len(clients_with_area)
            
        else:
            # Sem áreas cadastradas
            clients_by_area = {}
            clients_without_area = len(clients_data)
            total_clients = len(clients_data)
        
        stats = {
            'clients_by_area': clients_by_area,
            'clients_without_area': clients_without_area,
            'total_clients': total_clients
        }
        
    except Exception as e:
        print(f"Erro ao calcular estatísticas: {e}")
        stats = {
            'clients_by_area': {},
            'clients_without_area': 0,
            'total_clients': 0
        }
    
    return render_template('painel.html', stats=stats)

@main.route('/autenticado/painel/stats', methods=['GET'])
def painel_stats():
    """Endpoint API para obter estatísticas de clientes por área"""
    try:
        from ml.geo_utils import GeoUtils
        
        # Obtém o ID do usuário logado
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado',
                'clients_by_area': [],
                'clients_without_area': 0,
                'total_clients': 0
            }), 401
        
        # Tenta converter user_id para int
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Busca apenas os clientes do usuário logado (não pontos de base)
        clients = LatLong.query.filter_by(id_user=uid, user_point=False).all()
        clients_data = [{
            'id': c.id, 
            'latitude': c.latitude, 
            'longitude': c.longitude,
            'hash_client': c.hash_client
        } for c in clients]
        
        # Busca apenas os polígonos (áreas) do usuário logado
        polygons = Polygon.query.filter_by(user_id=uid).all()
        polygons_data = []
        
        for p in polygons:
            try:
                geojson = json.loads(p.geojson_data)
                
                # Extrai coordenadas do GeoJSON conforme o formato
                if geojson.get('type') == 'Feature':
                    geometry = geojson.get('geometry', {})
                    if geometry.get('type') == 'Polygon':
                        # GeoJSON Polygon tem coordenadas em [[[lon, lat], ...]]
                        coords_array = geometry.get('coordinates', [[]])[0]
                    elif geometry.get('type') == 'Rectangle':
                        # Retângulo também tem formato similar
                        coords_array = geometry.get('coordinates', [[]])[0]
                    else:
                        print(f"⚠️  Tipo de geometria não suportado: {geometry.get('type')}")
                        continue
                elif geojson.get('type') == 'Polygon':
                    coords_array = geojson.get('coordinates', [[]])[0]
                else:
                    print(f"⚠️  Tipo de GeoJSON não suportado: {geojson.get('type')}")
                    continue
                
                # Converte [lon, lat] para [lat, lon] como esperado pelo GeoUtils
                coords = [[c[1], c[0]] for c in coords_array] if coords_array else []
                
                if len(coords) >= 3:
                    polygons_data.append({
                        'id': p.id,
                        'name': p.group_name,
                        'coordinates': coords
                    })
                else:
                    print(f"⚠️  Área '{p.group_name}' tem menos de 3 coordenadas")
                    
            except Exception as e:
                print(f"❌ Erro ao processar área '{p.group_name}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Filtra clientes por área usando otimização
        if polygons_data:
            result = GeoUtils.filter_clients_by_polygons_optimized(
                clients_data, 
                polygons_data
            )
            
            # Calcula estatísticas
            clients_by_area = []
            clients_with_area = set()
            
            for polygon in polygons_data:
                poly_id = polygon['id']
                poly_name = polygon['name']
                clients_in_area = result.get(poly_id, [])
                count = len(clients_in_area)
                
                clients_by_area.append({
                    'area_name': poly_name,
                    'count': count
                })
                
                # Adiciona IDs ao set de clientes com área
                for client in clients_in_area:
                    clients_with_area.add(client.get('id'))
            
            # Calcula clientes sem área
            total_clients = len(clients_data)
            clients_without_area = total_clients - len(clients_with_area)
            
        else:
            # Sem áreas cadastradas
            clients_by_area = []
            clients_without_area = len(clients_data)
            total_clients = len(clients_data)
        
        return jsonify({
            'success': True,
            'clients_by_area': clients_by_area,
            'clients_without_area': clients_without_area,
            'total_clients': total_clients
        })
        
    except Exception as e:
        print(f"Erro ao calcular estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'clients_by_area': [],
            'clients_without_area': 0,
            'total_clients': 0
        })

@main.route('/autenticado/painel/novos-clientes', methods=['GET'])
def novos_clientes_stats():
    """Endpoint API para obter os 10 produtos mais vendidos"""
    try:
        from sqlalchemy import func
        
        # Obtém o ID do usuário logado
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado',
                'labels': [],
                'valores': []
            }), 401
        
        # Tenta converter user_id para int
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Busca os produtos mais vendidos agrupados por id_produto (conta ocorrências)
        produtos_vendidos = db.session.query(
            OrderHistory.id_produto,
            func.count(OrderHistory.id).label('total_vendas')
        ).filter(
            OrderHistory.user_id == uid,
            OrderHistory.id_produto.isnot(None),
            OrderHistory.id_produto != ''
        ).group_by(
            OrderHistory.id_produto
        ).order_by(
            func.count(OrderHistory.id).desc()
        ).all()
        
        if not produtos_vendidos:
            return jsonify({
                'success': True,
                'labels': [],
                'valores': [],
                'message': 'Nenhum histórico de vendas encontrado'
            })
        
        # Pega apenas os top 10 produtos
        labels = []
        valores = []
        
        top_10 = produtos_vendidos[:10]  # Limita aos 10 primeiros
        
        for produto in top_10:
            # Usa o ID do produto como label (encurta se necessário)
            produto_label = produto.id_produto[:35] if len(produto.id_produto) > 35 else produto.id_produto
            labels.append(produto_label)
            valores.append(int(produto.total_vendas))
        
        return jsonify({
            'success': True,
            'labels': labels,
            'valores': valores,
            'total_produtos': len(produtos_vendidos)
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular novos clientes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'months': [],
            'counts': []
        })

@main.route('/autenticado/painel/top-clientes', methods=['GET'])
def top_clientes_visitados():
    """Endpoint API para obter os clientes com maior valor gasto (histórico de vendas)"""
    try:
        from sqlalchemy import func
        
        # Obtém o ID do usuário logado
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado',
                'clientes': []
            }), 401
        
        # Tenta converter user_id para int
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Busca clientes com maior valor total gasto, agrupado por hash_cliente
        query_results = db.session.query(
            OrderHistory.hash_cliente,
            func.sum(OrderHistory.valor_total_item).label('valor_total'),
            func.max(OrderHistory.data_compra).label('ultima_compra'),
            func.count(OrderHistory.id).label('total_pedidos')
        ).filter(
            OrderHistory.user_id == uid,
            OrderHistory.hash_cliente.isnot(None),
            OrderHistory.hash_cliente != '',
            OrderHistory.valor_total_item.isnot(None)
        ).group_by(
            OrderHistory.hash_cliente
        ).order_by(
            func.sum(OrderHistory.valor_total_item).desc()
        ).limit(5).all()
        
        if not query_results:
            return jsonify({
                'success': True,
                'clientes': [],
                'message': 'Nenhum histórico de vendas encontrado'
            })
        
        # Busca informações dos clientes
        top_clientes = []
        for result in query_results:
            hash_cliente = result.hash_cliente
            valor_total = result.valor_total or 0
            ultima_compra = result.ultima_compra
            total_pedidos = result.total_pedidos
            
            # Busca info do cliente
            cliente = ClientName.query.filter_by(hash_client=hash_cliente).first()
            
            if cliente:
                # Formata data da última compra
                data_formatada = ''
                if ultima_compra:
                    data_formatada = ultima_compra.strftime('%d/%m/%Y')
                
                top_clientes.append({
                    'hash_client': hash_cliente,
                    'nome': cliente.name_client or 'Cliente sem nome',
                    'valor_total': round(valor_total, 2),
                    'total_pedidos': total_pedidos,
                    'ultima_compra': data_formatada,
                    'ultima_compra_timestamp': ultima_compra.isoformat() if ultima_compra else None
                })
        
        return jsonify({
            'success': True,
            'clientes': top_clientes
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular top clientes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'clientes': []
        })

@main.route('/autenticado/painel/formas-pagamento', methods=['GET'])
def formas_pagamento_stats():
    """Endpoint API para obter distribuição de formas de pagamento do histórico de vendas"""
    try:
        from collections import Counter
        
        # Obtém o ID do usuário logado
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado',
                'formas_pagamento': []
            }), 401
        
        # Tenta converter user_id para int
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Busca pedidos do usuário que têm forma de pagamento registrada
        pedidos = OrderHistory.query.filter(
            OrderHistory.user_id == uid,
            OrderHistory.tipos_pagamento.isnot(None),
            OrderHistory.tipos_pagamento != ''
        ).all()
        
        if not pedidos:
            return jsonify({
                'success': True,
                'formas_pagamento': [],
                'total_pedidos': 0,
                'message': 'Nenhum histórico de vendas encontrado'
            })
        
        # Contador de formas de pagamento
        pagamentos_counter = Counter()
        
        for pedido in pedidos:
            # tipos_pagamento pode conter múltiplos tipos separados por vírgula
            tipos = pedido.tipos_pagamento.split(',') if pedido.tipos_pagamento else []
            for tipo in tipos:
                tipo_limpo = tipo.strip()
                if tipo_limpo:
                    pagamentos_counter[tipo_limpo] += 1
        
        # Prepara dados para o gráfico
        labels = []
        values = []
        total = sum(pagamentos_counter.values())
        
        # Pega os top 5 mais usados
        for forma, count in pagamentos_counter.most_common(5):
            labels.append(forma)
            values.append(count)
        
        # Calcula percentuais
        percentuais = [round((v / total) * 100, 1) if total > 0 else 0 for v in values]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'values': values,
            'percentuais': percentuais,
            'total_pedidos': len(pedidos),
            'total_pagamentos': total
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular formas de pagamento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'formas_pagamento': []
        })

@main.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Busca usuário pelo email
        from base.models import User
        user = User.query.filter_by(email=form.email.data).first()
        
        # Verifica se usuário existe e senha está correta
        if user and user.check_password(form.password.data):
            # Atualiza último login
            user.update_last_login()
            
            # IMPORTANTE: Login com Flask-Login
            login_user(user, remember=True)
            
            # Configura sessão (mantém para compatibilidade)
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            session.permanent = True
            
            # Log de login bem-sucedido
            from base.models import SystemLog
            log = SystemLog(
                user_id=user.id,
                action='login',
                resource='sistema',
                details=f'Login bem-sucedido: {user.email}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                level='INFO'
            )
            db.session.add(log)
            db.session.commit()
            
            return redirect(url_for('main.painel'))
        else:
            # Login falhou - usuário ou senha incorretos
            from flask import flash
            flash('Email ou senha incorretos. Tente novamente.', 'danger')
            
            # Log de tentativa de login falha (se usuário existe)
            if user:
                from base.models import SystemLog
                log = SystemLog(
                    user_id=user.id,
                    action='login_failed',
                    resource='sistema',
                    details=f'Tentativa de login falha: {form.email.data}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    level='WARNING'
                )
                db.session.add(log)
                db.session.commit()
    
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    """Rota para fazer logout do sistema"""
    user_id = session.get('user_id')
    email = session.get('email')
    
    # Log de logout
    if user_id:
        from base.models import SystemLog
        log = SystemLog(
            user_id=user_id,
            action='logout',
            resource='sistema',
            details=f'Logout: {email}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            level='INFO'
        )
        db.session.add(log)
        db.session.commit()
    
    # IMPORTANTE: Logout do Flask-Login
    logout_user()
    
    # Limpa sessão
    session.clear()
    
    from flask import flash
    flash('Você saiu do sistema com sucesso.', 'success')
    return redirect(url_for('main.login'))

@main.route('/registro', methods=['GET', 'POST'])
def registro():
    from base.forms import RegistrationForm
    from base.models import User, SystemLog
    from flask import flash
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Verifica se email já existe
        existing_user_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_email:
            flash('Este email já está cadastrado. Tente fazer login.', 'warning')
            return render_template('registro.html', form=form)
        
        # Verifica se username já existe
        existing_user_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_username:
            flash('Este nome de usuário já está em uso. Escolha outro.', 'warning')
            return render_template('registro.html', form=form)
        
        try:
            # Cria novo usuário
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                role='user',  # Usuários novos começam como 'user'
                is_active=True
            )
            new_user.set_password(form.password.data)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Log de registro
            log = SystemLog(
                user_id=new_user.id,
                action='register',
                resource='sistema',
                details=f'Novo usuário registrado: {new_user.email}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                level='INFO'
            )
            db.session.add(log)
            db.session.commit()
            
            # Mensagem de sucesso
            flash(f'Conta criada com sucesso! Bem-vindo, {new_user.username}!', 'success')
            
            # Faz login automático após registro
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['email'] = new_user.email
            session.permanent = True
            
            return redirect(url_for('main.painel'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {str(e)}', 'danger')
            print(f"Erro no registro: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('registro.html', form=form)

@main.route('/autenticado/documentacao')
def documentacao():
    return render_template('documentacao.html')

@main.route('/autenticado/pontosSaida', methods=['GET', 'POST', 'PUT', 'DELETE'])
def pontosSaida():
    user_id = session.get('user_id', 'anon')
    
    # GET - Listar pontos base do usuário
    if request.method == 'GET' and request.args.get('action') == 'list':
        try:
            # Converte user_id
            try:
                uid = int(user_id)
            except:
                uid = user_id
            
            # Busca pontos base (user_point=True)
            pontos = LatLong.query.filter_by(id_user=uid, user_point=True).all()
            
            resultado = []
            for p in pontos:
                resultado.append({
                    'id': p.id,
                    'nome': f'Ponto Base {p.id}',  # Vamos adicionar campo nome depois
                    'latitude': p.latitude,
                    'longitude': p.longitude,
                    'hash_client': p.hash_client or 'BASE',
                    'created_at': p.created_at.isoformat() if p.created_at else None
                })
            
            return jsonify({'success': True, 'pontos': resultado})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # POST - Criar novo ponto base
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': 'Dados não recebidos'})
            
            # Validações
            nome = data.get('nome', '').strip()
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            range_km = data.get('range', 10)
            
            if not nome or latitude is None or longitude is None:
                return jsonify({'success': False, 'error': 'Dados obrigatórios não fornecidos'})
            
            # Converte user_id
            try:
                uid = int(user_id)
            except:
                uid = user_id
            
            # Cria novo ponto base usando hash_client para armazenar nome
            novo_ponto = LatLong(
                id_user=uid,
                hash_client=nome,  # Armazena nome temporariamente aqui
                latitude=float(latitude),
                longitude=float(longitude),
                user_point=True  # Marca como ponto base
            )
            
            db.session.add(novo_ponto)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Ponto Base "{nome}" criado com sucesso!',
                'data': {
                    'id': novo_ponto.id,
                    'nome': nome,
                    'latitude': novo_ponto.latitude,
                    'longitude': novo_ponto.longitude,
                    'range_km': range_km
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Erro ao criar: {str(e)}'}), 500
    
    # PUT - Atualizar ponto base
    if request.method == 'PUT':
        try:
            ponto_id = request.args.get('id')
            data = request.get_json()
            
            if not ponto_id:
                return jsonify({'success': False, 'error': 'ID não fornecido'}), 400
            
            # Converte user_id
            try:
                uid = int(user_id)
            except:
                uid = user_id
            
            # Busca o ponto (verifica se pertence ao usuário)
            ponto = LatLong.query.filter_by(id=ponto_id, id_user=uid, user_point=True).first()
            
            if not ponto:
                return jsonify({'success': False, 'error': 'Ponto não encontrado'}), 404
            
            # Atualiza campos
            if 'nome' in data:
                ponto.hash_client = data['nome']
            if 'latitude' in data:
                ponto.latitude = float(data['latitude'])
            if 'longitude' in data:
                ponto.longitude = float(data['longitude'])
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Ponto Base atualizado com sucesso!',
                'data': {
                    'id': ponto.id,
                    'nome': ponto.hash_client,
                    'latitude': ponto.latitude,
                    'longitude': ponto.longitude
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Erro ao atualizar: {str(e)}'}), 500
    
    # DELETE - Excluir ponto base
    if request.method == 'DELETE':
        try:
            ponto_id = request.args.get('id')
            
            if not ponto_id:
                return jsonify({'success': False, 'error': 'ID não fornecido'}), 400
            
            # Converte user_id
            try:
                uid = int(user_id)
            except:
                uid = user_id
            
            # Busca e deleta (verifica se pertence ao usuário)
            ponto = LatLong.query.filter_by(id=ponto_id, id_user=uid, user_point=True).first()
            
            if not ponto:
                return jsonify({'success': False, 'error': 'Ponto não encontrado'}), 404
            
            db.session.delete(ponto)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Ponto Base excluído com sucesso!'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Erro ao excluir: {str(e)}'}), 500
    
    # GET - Retorna a página
    return render_template('pontobase.html')


@main.route('/autenticado/clientes', methods=['GET', 'POST', 'DELETE'])
def clientes():
    # DELETE - Excluir cliente
    if request.method == 'DELETE':
        try:
            data = request.get_json()
            hash_client = data.get('hash_client')
            user_id = data.get('user_id') or session.get('user_id', 'anon')
            
            if not hash_client:
                return jsonify({'success': False, 'error': 'Hash do cliente não fornecido'}), 400
            
            # Buscar e excluir o cliente
            client = ClientName.query.filter_by(hash_client=hash_client, user_id=user_id).first()
            if not client:
                return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
            
            db.session.delete(client)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Cliente excluído com sucesso'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # GET - Lista de clientes ou adicionar cliente manualmente
    if request.method == 'GET':
        # GET ?action=get - Retorna lista de clientes
        if request.args.get('action') == 'get':
            try:
                user_id = request.args.get('user_id') or session.get('user_id', 'anon')
                if not user_id:
                    return jsonify({'success': True, 'clients': []})
                
                # Aceita tanto string quanto int para user_id (não converte mais para int)
                clients = ClientName.query.filter_by(user_id=user_id).all()
                data = []
                for c in clients:
                    data.append({
                        'name_client': c.name_client,
                        'hash_client': c.hash_client,
                        'cidade': c.cidade,
                        'estado': c.estado,
                        'created_at': c.created_at.isoformat() if c.created_at else None
                    })
                return jsonify({'success': True, 'clients': data})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # GET sem action - Retorna a página HTML
        return render_template('clientes.html')
    
    # POST - Upload de arquivo ou adicionar cliente manualmente
    if request.method == 'POST':
        # POST ?action=add - Adicionar cliente manualmente
        if request.args.get('action') == 'add':
            try:
                data = request.get_json()
                name_client = data.get('name_client')
                cidade = data.get('cidade')
                estado = data.get('estado', '').upper()
                user_id = data.get('user_id') or session.get('user_id', 'anon')
                
                if not name_client or not cidade or not estado:
                    return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios'}), 400
                
                # Gerar hash único para o cliente
                import hashlib
                hash_base = f"{name_client}_{cidade}_{estado}_{user_id}_{datetime.now().isoformat()}"
                hash_client = hashlib.md5(hash_base.encode()).hexdigest()
                
                # Criar novo cliente
                new_client = ClientName(
                    name_client=name_client,
                    hash_client=hash_client,
                    user_id=user_id,
                    cidade=cidade,
                    estado=estado,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.session.add(new_client)
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Cliente adicionado com sucesso',
                    'client': {
                        'name_client': name_client,
                        'hash_client': hash_client,
                        'cidade': cidade,
                        'estado': estado,
                        'created_at': new_client.created_at.isoformat()
                    }
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
            
        # POST - Upload de arquivo Excel/CSV para importar clientes
        # POST sem action (upload de arquivo)
        if 'file' in request.files:
            try:
                file = request.files['file']
                if file.filename == '':
                    flash('Arquivo vazio', 'danger')
                    return redirect(url_for('main.clientes'))

                fname = file.filename.lower()
                if fname.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                # normaliza colunas do arquivo
                cols_map = {c.lower().strip(): c for c in df.columns}

                def find_col(*candidates):
                    for cand in candidates:
                        key = cand.lower().strip()
                        if key in cols_map:
                            return cols_map[key]
                    return None

                nome_col = find_col('nome', 'name', 'name_client', 'cliente', 'nome do cliente')
                cidade_col = find_col('cidade', 'city')
                estado_col = find_col('estado', 'uf', 'state')

                if not nome_col or not cidade_col or not estado_col:
                    flash(f'Colunas esperadas não encontradas. Encontradas: {list(df.columns)}', 'danger')
                    return redirect(url_for('main.clientes'))

                # colunas possíveis de latitude/longitude no arquivo
                lat_col = find_col('latitude', 'lat', 'latitud')
                lon_col = find_col('longitude', 'lon', 'lng', 'longitud')

                registros = 0
                user_id = session.get('user_id', 'anon')
                try:
                    uid = int(user_id)
                except:
                    uid = user_id

                # colunas válidas do modelo ClientName (evita atribuir campos inexistentes)
                valid_client_cols = set(col.name for col in ClientName.__table__.columns)

                for _, row in df.iterrows():
                    name_client = str(row.get(nome_col, '')).strip()
                    cidade = str(row.get(cidade_col, '')).strip()
                    estado = str(row.get(estado_col, '')).strip().upper()

                    if not name_client or not cidade or not estado:
                        continue

                    # evita duplicatas pelo trio + user
                    existe = ClientName.query.filter_by(
                        name_client=name_client,
                        cidade=cidade,
                        estado=estado,
                        user_id=uid
                    ).first()
                    if existe:
                        continue

                    # aqui, conforme seu ajuste atual, hash_client = name_client
                    hash_client = name_client

                    # monta kwargs apenas com campos do modelo ClientName
                    client_kwargs = {
                        'name_client': name_client,
                        'hash_client': hash_client,
                        'user_id': uid,
                        'cidade': cidade,
                        'estado': estado,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }

                    # preenche outros campos do modelo se existirem no arquivo (mapeamento seguro)
                    for model_col in valid_client_cols:
                        if model_col in client_kwargs or model_col in ('id', 'created_at', 'updated_at'):
                            continue
                        file_col = cols_map.get(model_col.lower())
                        if file_col:
                            val = row.get(file_col)
                            if pd.notna(val) and str(val).strip() != '':
                                client_kwargs[model_col] = val

                    new_client = ClientName(**client_kwargs)
                    db.session.add(new_client)
                    registros += 1

                    # se arquivo tiver lat/lon, crie registro em LatLong (somente se ambos existirem)
                    if lat_col and lon_col:
                        lat_val = row.get(lat_col)
                        lon_val = row.get(lon_col)
                        if pd.notna(lat_val) and pd.notna(lon_val):
                            try:
                                lat_f = float(lat_val)
                                lon_f = float(lon_val)
                                loc = LatLong(
                                    id_user=uid,
                                    hash_client=hash_client,
                                    latitude=lat_f,
                                    longitude=lon_f,
                                    user_point=False,
                                    created_at=datetime.now()
                                )
                                db.session.add(loc)
                            except Exception:
                                # ignora valores inválidos de coordenada
                                pass

                db.session.commit()
                flash(f'{registros} clientes importados com sucesso!', 'success')
                return redirect(url_for('main.clientes'))

            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao importar clientes: {str(e)}', 'danger')
                return redirect(url_for('main.clientes'))

        
        # POST ?action=edit - Editar cliente
        if request.args.get('action') == 'edit':
            try:
                data = request.get_json()
                hash_client = data.get('hash_client')
                name_client = data.get('name_client')
                cidade = data.get('cidade')
                estado = data.get('estado', '').upper()
                user_id = data.get('user_id') or session.get('user_id', 'anon')
                if not hash_client or not name_client or not cidade or not estado:
                    return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios'}), 400
                client = ClientName.query.filter_by(hash_client=hash_client, user_id=user_id).first()
                if not client:
                    return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
                client.name_client = name_client
                client.cidade = cidade
                client.estado = estado
                client.updated_at = datetime.now()
                db.session.commit()
                return jsonify({'success': True, 'message': 'Cliente editado com sucesso'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500
    
    # GET - mostrar página com estatísticas
    user_id = User.query.get(int(user_id))  # Em produção, pegar da sessão
    stats = get_estatisticas_usuario(user_id)
    
    return render_template('clientes.html', stats=stats)

@main.route('/autenticado/configuracoes')
def configuracoes():
    return render_template('configuracoes.html')


@main.route('/api/latlongs')
def api_latlongs():
    """Retorna pontos de lat/long para um usuário em JSON.
    Query params:
      - user_id (opcional) : se omitido, usa sessão
    """
    user_id = request.args.get('user_id') or session.get('user_id')
    try:
        if not user_id:
            return jsonify({'success': True, 'points': []})

        # Se user_id não for número (ex: 'anon'), retorna lista vazia
        try:
            uid = int(user_id)
        except Exception:
            return jsonify({'success': True, 'points': []})

        points = LatLong.query.filter_by(id_user=uid).all()
        data = []
        for p in points:
            data.append({
                'id': p.id,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'user_point': bool(p.user_point),
                'hash_client': p.hash_client
            })

        return jsonify({'success': True, 'points': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main.route('/autenticado/area-statistics', methods=['POST'])
def get_area_statistics():
    """
    Retorna estatísticas de vendas para uma lista de clientes (hashes)
    Usado quando o usuário seleciona um polígono no mapa
    
    IMPORTANTE: OrderHistory e ClientName estão em bancos diferentes,
    então fazemos queries separadas e processamos os dados em memória.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        clientes_hashes = data.get('clientes', [])
        
        print(f"📊 [STATS] User: {user_id} | Clientes: {len(clientes_hashes)}")
        print(f"📊 [STATS] Hashes recebidos: {clientes_hashes[:3]}..." if len(clientes_hashes) > 3 else f"📊 [STATS] Hashes: {clientes_hashes}")
        
        # Tenta converter user_id
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Se não há clientes, retorna zeros
        if not clientes_hashes:
            return jsonify({
                'success': True,
                'total_clientes': 0,
                'total_pedidos': 0,
                'valor_total': 0.0,
                'ticket_medio': 0.0,
                'ultima_compra': None
            })
        
        # Busca TODAS as vendas deste usuário (sem filtro de hash primeiro)
        # para debug
        total_vendas_usuario = OrderHistory.query.filter_by(user_id=uid).count()
        print(f"[STATS] Total de vendas do usuário {uid}: {total_vendas_usuario}")
        
        # Busca dados do histórico de vendas FILTRADO pelos hashes
        vendas = OrderHistory.query.filter(
            OrderHistory.user_id == uid,
            OrderHistory.hash_cliente.in_(clientes_hashes)
        ).all()
        
        print(f"[STATS] Vendas encontradas: {len(vendas)}")
        
        # Se não há vendas, retorna zeros
        if not vendas:
            print(f"[STATS] Nenhuma venda encontrada para os hashes fornecidos")
            # Debug: mostra alguns hashes do banco
            sample_vendas = OrderHistory.query.filter_by(user_id=uid).limit(3).all()
            if sample_vendas:
                print(f"[STATS] Exemplo de hashes no banco:")
                for v in sample_vendas:
                    print(f"   - {v.hash_cliente}")
            
            return jsonify({
                'success': True,
                'total_clientes': 0,
                'total_pedidos': 0,
                'valor_total': 0.0,
                'ticket_medio': 0.0,
                'ultima_compra': None
            })
        
        # Processa dados em memória
        clientes_unicos = set()
        total_pedidos = 0
        valores = []
        datas = []
        
        for venda in vendas:
            clientes_unicos.add(venda.hash_cliente)
            total_pedidos += 1
            
            if venda.valor_total_pagamento:
                valores.append(float(venda.valor_total_pagamento))
            
            if venda.data_compra:
                datas.append(venda.data_compra)
        
        valor_total = sum(valores) if valores else 0.0
        ticket_medio = (valor_total / len(valores)) if valores else 0.0
        
        # Formata a última compra
        ultima_compra_str = None
        if datas:
            # Ordena e pega a mais recente
            datas_ordenadas = sorted(datas, reverse=True)
            ultima = datas_ordenadas[0]
            
            try:
                if isinstance(ultima, datetime):
                    ultima_compra_str = ultima.strftime('%d/%m/%Y')
                else:
                    dt = datetime.strptime(str(ultima), '%Y-%m-%d %H:%M:%S')
                    ultima_compra_str = dt.strftime('%d/%m/%Y')
            except:
                ultima_compra_str = str(ultima)
        
        result = {
            'success': True,
            'total_clientes': len(clientes_unicos),
            'total_pedidos': total_pedidos,
            'valor_total': valor_total,
            'ticket_medio': ticket_medio,
            'ultima_compra': ultima_compra_str
        }
        
        print(f"[STATS] Resultado: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[STATS] Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'total_clientes': 0,
            'total_pedidos': 0,
            'valor_total': 0.0,
            'ticket_medio': 0.0,
            'ultima_compra': None
        }), 500


@main.route('/autenticado/historicovendas', methods=['GET', 'POST', 'DELETE'])
def historicovendas():
    """
    Gerencia importação de histórico de vendas via Excel
    
    POST: Upload de arquivo Excel → ETL → Inserção no OrderHistory → Cálculo de Scores RFM
    GET: API para listar vendas (?action=get) ou renderizar template
    DELETE: Excluir venda específica (?action=delete)
    """
    # Validar sessão
    user_id = session.get('user_id')
    if not user_id:
        flash('⚠️ Sessão expirada. Faça login novamente.', 'warning')
        return redirect(url_for('main.login'))
    
    uid = int(user_id)
    
    # API GET: Listar vendas
    if request.method == 'GET' and request.args.get('action') == 'get':
        try:
            vendas = OrderHistory.query.filter_by(user_id=uid).order_by(
                OrderHistory.data_compra.desc()
            ).all()
            
            vendas_list = []
            for v in vendas:
                vendas_list.append({
                    'id': v.id,
                    'id_pedido': v.id_pedido,
                    'hash_cliente': v.hash_cliente,
                    'id_cliente': v.id_cliente,
                    'id_produto': v.id_produto,
                    'data_compra': v.data_compra.isoformat() if v.data_compra else None,
                    'valor_total_pagamento': float(v.valor_total_pagamento) if v.valor_total_pagamento else 0,
                    'status_pedido': v.status_pedido,
                    'estado_cliente': v.estado_cliente,
                    'cidade_cliente': v.cidade_cliente,
                    'nota_avaliacao': v.nota_avaliacao,
                    'tipos_pagamento': v.tipos_pagamento,
                    'created_at': v.created_at.isoformat() if hasattr(v, 'created_at') and v.created_at else None
                })
            
            return jsonify({'success': True, 'vendas': vendas_list})
        except Exception as e:
            logger.error(f"Erro ao listar vendas: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # API DELETE: Excluir venda
    if request.method == 'DELETE' or (request.method == 'GET' and request.args.get('action') == 'delete'):
        try:
            data = request.get_json() if request.method == 'DELETE' else request.args
            venda_id = data.get('id')
            
            if not venda_id:
                return jsonify({'success': False, 'error': 'ID não fornecido'}), 400
            
            venda = OrderHistory.query.filter_by(id=venda_id, user_id=uid).first()
            
            if not venda:
                return jsonify({'success': False, 'error': 'Venda não encontrada'}), 404
            
            db.session.delete(venda)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Venda excluída com sucesso'})
        except Exception as e:
            logger.error(f"Erro ao excluir venda: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    if request.method == 'POST':
        # Validar upload de arquivo
        if 'file' not in request.files:
            flash('❌ Nenhum arquivo enviado', 'danger')
            return redirect(url_for('main.historicovendas'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('❌ Arquivo vazio', 'danger')
            return redirect(url_for('main.historicovendas'))
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('❌ Formato inválido. Use Excel (.xlsx ou .xls)', 'danger')
            return redirect(url_for('main.historicovendas'))
        
        try:
            # Salvar arquivo temporário
            filename = secure_filename(file.filename)
            temp_path = os.path.join('temp', filename)
            os.makedirs('temp', exist_ok=True)
            file.save(temp_path)
            
            logger.info(f"📂 Arquivo salvo: {temp_path}")
            
            # Ler Excel
            df = pd.read_excel(temp_path)
            logger.info(f"📊 Excel carregado: {len(df)} linhas")
            
            # Validar colunas obrigatórias (hash_cliente copiado de id_cliente)
            colunas_obrigatorias = ['id_pedido', 'id_cliente', 'data_compra', 'valor_total_pagamento']
            colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
            
            if colunas_faltantes:
                flash(f'❌ Colunas obrigatórias faltando: {", ".join(colunas_faltantes)}', 'danger')
                os.remove(temp_path)
                return redirect(url_for('main.historicovendas'))
            
            # Processar e inserir vendas
            registros_inseridos = 0
            registros_duplicados = 0
            batch_size = 100
            
            for idx in range(0, len(df), batch_size):
                batch = df.iloc[idx:idx + batch_size]
                
                for _, row in batch.iterrows():
                    try:
                        # Verificar duplicatas (id_pedido + user_id)
                        existe = OrderHistory.query.filter_by(
                            id_pedido=str(row['id_pedido']),
                            user_id=uid
                        ).first()
                        
                        if existe:
                            registros_duplicados += 1
                            continue
                        
                        # Hash do cliente = cópia direta do id_cliente (sem transformação)
                        hash_cliente = str(row['id_cliente'])
                        
                        # Criar registro de venda
                        venda = OrderHistory(
                            user_id=uid,
                            id_pedido=str(row['id_pedido']),
                            hash_cliente=hash_cliente,
                            id_cliente=str(row.get('id_cliente', '')),
                            id_unico_cliente=str(row.get('id_unico_cliente', row.get('id_cliente', ''))),
                            id_produto=str(row.get('id_produto', '')),
                            data_compra=pd.to_datetime(row['data_compra']) if pd.notna(row.get('data_compra')) else None,
                            valor_total_pagamento=float(row['valor_total_pagamento']) if pd.notna(row.get('valor_total_pagamento')) else 0,
                            nota_avaliacao=int(row['nota_avaliacao']) if pd.notna(row.get('nota_avaliacao')) else None,
                            status_pedido=str(row.get('status_pedido', '')),
                            tipos_pagamento=str(row.get('tipos_pagamento', row.get('metodo_pagamento', ''))),
                            cidade_cliente=str(row.get('cidade_cliente', '')),
                            estado_cliente=str(row.get('estado_cliente', '')),
                            cep_cliente=str(row.get('cep_cliente', ''))
                        )
                        
                        db.session.add(venda)
                        registros_inseridos += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar linha {idx}: {str(e)}")
                        continue
                
                # Commit do batch
                db.session.commit()
            
            # Limpar arquivo temporário
            os.remove(temp_path)
            
            # Feedback ao usuário
            if registros_inseridos > 0:
                flash(f'✅ {registros_inseridos} registros de vendas importados!', 'success')
                
                if registros_duplicados > 0:
                    flash(f'ℹ️ {registros_duplicados} registros duplicados ignorados', 'info')
                
                # ✅ INTEGRAÇÃO RFM: Calcular scores após importação bem-sucedida
                try:
                    from ml.client_scoring import calcular_scores_para_usuario
                    
                    logger.info(f"🧠 Iniciando cálculo de scores RFM para user_id={uid}")
                    resultado = calcular_scores_para_usuario(user_id=uid)
                    
                    # Feedback detalhado
                    flash(
                        f'🧠 Scores RFM calculados: {resultado["clientes_analisados"]} clientes | '
                        f'Score médio: {resultado["score_medio"]:.1f} | '
                        f'Distribuição: {resultado["distribuicao"]}',
                        'info'
                    )
                    
                    logger.info(f"✅ Scores calculados: {resultado}")
                    
                except Exception as e:
                    logger.error(f"⚠️ Erro ao calcular scores RFM: {str(e)}", exc_info=True)
                    flash(
                        f'⚠️ Vendas importadas mas scores não calculados. '
                        f'Execute manualmente: python -c "from ml.client_scoring import calcular_scores_para_usuario; calcular_scores_para_usuario({uid})"',
                        'warning'
                    )
            else:
                flash('⚠️ Nenhum registro novo foi importado', 'warning')
            
            return redirect(url_for('main.historicovendas'))
            
        except Exception as e:
            logger.error(f"❌ Erro geral no upload: {str(e)}", exc_info=True)
            flash(f'❌ Erro ao processar arquivo: {str(e)}', 'danger')
            
            # Limpar arquivo se existir
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            db.session.rollback()
            return redirect(url_for('main.historicovendas'))
    
    # GET padrão: Renderizar template (não é uma chamada API)
    return render_template('historicovendas.html')

@main.route('/autenticado/historicovendas/baixar-modelo')
def baixar_modelo_historico():
    """Gera e retorna o arquivo Excel modelo para importação de histórico de vendas"""
    try:
        import pandas as pd
        from io import BytesIO
        from datetime import datetime
        
        # Definir estrutura do modelo
        exemplo = {
            'id_pedido': 'exemplo_pedido_001',
            'id_item_pedido': 1,
            'id_cliente': 'exemplo_cliente_001',
            'id_unico_cliente': 'exemplo_unico_001',
            'id_produto': 'exemplo_produto_001',
            'data_compra': '2024-01-15 10:30:00',
            'data_aprovacao': '2024-01-15 11:00:00',
            'data_envio_transportadora': '2024-01-16 09:00:00',
            'data_entrega_cliente': '2024-01-20 14:30:00',
            'data_estimada_entrega': '2024-01-22 23:59:59',
            'data_limite_envio': '2024-01-17 23:59:59',
            'status_pedido': 'delivered',
            'tempo_entrega_dias': 5,
            'atraso_entrega_dias': -2,
            'ano_compra': 2024,
            'mes_compra': 1,
            'ano_mes_compra': '2024-01',
            'dia_semana_compra': 0,
            'preco': 99.90,
            'valor_frete': 15.50,
            'valor_total_item': 115.40,
            'valor_total_pagamento': 115.40,
            'num_pagamentos': 1,
            'tipos_pagamento': 'credit_card',
            'max_parcelas': 3,
            'cidade_cliente': 'Brasília',
            'estado_cliente': 'DF',
            'cep_cliente': '70000',
            'nota_avaliacao': 5,
            'titulo_comentario': 'Excelente produto!',
            'mensagem_comentario': 'Produto chegou antes do prazo e em perfeitas condições.',
            'data_criacao_avaliacao': '2024-01-21 10:00:00',
            'data_resposta_avaliacao': '2024-01-21 15:00:00'
        }
        
        # Criar DataFrame com linha de exemplo
        df_modelo = pd.DataFrame([exemplo])
        
        # Gerar arquivo Excel em memória
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_modelo.to_excel(writer, index=False, sheet_name='Histórico de Vendas')
        output.seek(0)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'modelo_historico_vendas_{timestamp}.xlsx'
        
        # Retornar arquivo para download
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Erro ao gerar modelo: {str(e)}', 'error')
        return redirect(url_for('main.historicovendas'))

@main.route('/autenticado/roteirizacao')
def roteirizacao():
    """Página de roteirização de vendas"""
    # 🔍 DEBUG: Verificar sessão ao carregar página
    logger.info(f"🔍 [ROTEIRIZACAO PAGE] Session keys: {list(session.keys())}")
    logger.info(f"🔍 [ROTEIRIZACAO PAGE] user_id na sessão: {session.get('user_id')}")
    return render_template('roteirizacao.html')

@main.route('/autenticado/roteirizacao/grupos', methods=['GET'])
def roteirizacao_get_grupos():
    """
    API específica para roteirização: retorna apenas polígonos/áreas do usuário.
    Usado na etapa 1 da roteirização para seleção de grupos.
    """
    try:
        # 🔍 DEBUG: Verificar estado da sessão
        logger.info(f"🔍 [ROTEIRIZAÇÃO] Session keys: {list(session.keys())}")
        logger.info(f"🔍 [ROTEIRIZAÇÃO] Session data: {dict(session)}")
        
        user_id = session.get('user_id')
        
        if not user_id:
            logger.warning("⚠️ [ROTEIRIZAÇÃO] user_id não encontrado na sessão")
            logger.warning(f"⚠️ [ROTEIRIZAÇÃO] Conteúdo completo da sessão: {dict(session)}")
            return jsonify({'success': False, 'error': 'Não autenticado', 'grupos': []}), 401
        
        # Converter user_id
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        logger.info(f"🎯 [ROTEIRIZAÇÃO] Buscando grupos para user_id: {uid}")
        
        # Buscar APENAS polígonos do usuário (não clientes)
        polygons = Polygon.query.filter_by(user_id=uid).order_by(Polygon.created_at.desc()).all()
        
        logger.info(f"📊 [ROTEIRIZAÇÃO] Encontrados {len(polygons)} polígonos no banco")
        
        if not polygons:
            logger.warning(f"⚠️ [ROTEIRIZAÇÃO] Nenhum grupo encontrado para user_id: {uid}")
            return jsonify({
                'success': True, 
                'grupos': [],
                'message': 'Nenhum grupo criado ainda. Crie grupos na página de Gestão de Grupos primeiro.'
            })
        
        result = []
        for p in polygons:
            try:
                geojson = json.loads(p.geojson_data)
                
                # Validar se GeoJSON tem coordenadas válidas
                coords = []
                if isinstance(geojson, dict):
                    geometry = geojson.get('geometry', {})
                    if geometry:
                        coords_raw = geometry.get('coordinates', [])
                        if coords_raw and len(coords_raw) > 0:
                            # Formato GeoJSON: [[[lon, lat], ...]]
                            # Pega o anel externo (primeiro array)
                            coords = coords_raw[0] if len(coords_raw) > 0 else []
                
                # Verificar se tem pelo menos 3 pontos (polígono válido)
                if not coords or len(coords) < 3:
                    logger.warning(f"⚠️ [ROTEIRIZAÇÃO] Polígono {p.id} '{p.group_name}' tem coordenadas inválidas ({len(coords)} pontos)")
                    continue
                
                # Adicionar à lista
                grupo = {
                    'id': p.id,
                    'name': p.group_name,
                    'coordinates': coords,  # [[[lon, lat], ...]]
                    'geojson': geojson,  # GeoJSON completo
                    'created_at': p.created_at.isoformat() if p.created_at else None
                }
                
                result.append(grupo)
                logger.info(f"   ✓ Polígono {p.id}: '{p.group_name}' ({len(coords)} pontos)")
                
            except json.JSONDecodeError as e:
                logger.error(f"   ✗ Erro ao decodificar JSON do polígono {p.id}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"   ✗ Erro ao processar polígono {p.id}: {str(e)}")
                continue
        
        logger.info(f"✅ [ROTEIRIZAÇÃO] Retornando {len(result)} grupos válidos")
        
        return jsonify({
            'success': True,
            'grupos': result,
            'total': len(result)
        })
        
    except Exception as e:
        logger.error(f"❌ [ROTEIRIZAÇÃO] Erro ao buscar grupos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'grupos': []
        }), 500

@main.route('/autenticado/roteirizacao/filter', methods=['POST'])
def filter_clients_by_areas():
    data = request.json
    selected_ids = data.get('polygon_ids', [])
    
    # Obtém user_id da sessão
    user_id = session.get('user_id', 'anon')
    try:
        uid = int(user_id)
    except:
        uid = user_id
    
    # Busca apenas clientes do usuário logado
    clients = LatLong.query.filter_by(id_user=uid, user_point=False).all()
    clients_data = [{'id': c.id, 'latitude': c.latitude, 'longitude': c.longitude} 
                    for c in clients]
    
    # Busca apenas polígonos do usuário logado que estão na seleção
    polygons = Polygon.query.filter(
        Polygon.id.in_(selected_ids),
        Polygon.user_id == uid
    ).all()
    polygons_data = [{'id': p.id, 'coordinates': json.loads(p.geojson_data)} 
                     for p in polygons]
    
    # Filtra com otimização
    from ml.geo_utils import GeoUtils
    result = GeoUtils.filter_clients_by_polygons_optimized(
        clients_data, 
        polygons_data
    )
    
    # Retorna contagens
    counts = {pid: len(clients) for pid, clients in result.items()}
    return jsonify({'counts': counts})

@main.route('/autenticado/roteirizacao/processar', methods=['POST'])
def processar_roteirizacao():
    """Processa roteirização usando K-Means clustering com filtro de tamanho"""
    try:
        data = request.json
        dias = data.get('dias')
        grupos_selecionados = data.get('grupos_selecionados', [])
        max_clients_per_day = data.get('max_clients_per_day')  # Opcional
        
        # Obtém user_id da sessão
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Usuário não autenticado'
            }), 401
        
        try:
            uid = int(user_id)
        except:
            uid = user_id
        
        # Validações
        if not dias or not isinstance(dias, int) or dias <= 0:
            return jsonify({
                'success': False,
                'error': 'Número de dias inválido'
            }), 400
        
        if dias > 30:
            return jsonify({
                'success': False,
                'error': 'Número máximo de dias é 30'
            }), 400
        
        # Valida max_clients_per_day se fornecido
        if max_clients_per_day is not None:
            if not isinstance(max_clients_per_day, int) or max_clients_per_day < 1 or max_clients_per_day > 100:
                return jsonify({
                    'success': False,
                    'error': 'Máximo de clientes por dia deve estar entre 1 e 100'
                }), 400
        
        if not grupos_selecionados or len(grupos_selecionados) == 0:
            return jsonify({
                'success': False,
                'error': 'Nenhum grupo selecionado'
            }), 400
        
        # Busca apenas os clientes do usuário logado
        clients = LatLong.query.filter_by(id_user=uid, user_point=False).all()
        
        if not clients:
            return jsonify({
                'success': False,
                'error': 'Nenhum cliente cadastrado'
            }), 400
        
        # Prepara DataFrame com clientes
        import pandas as pd
        clients_data = [{
            'id': c.id,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'hash_client': c.hash_client
        } for c in clients]
        df_clientes = pd.DataFrame(clients_data)
        
        # Busca apenas polígonos do usuário logado que estão selecionados
        polygons = Polygon.query.filter(
            Polygon.id.in_(grupos_selecionados),
            Polygon.user_id == uid
        ).all()
        
        if not polygons:
            return jsonify({
                'success': False,
                'error': 'Grupos selecionados não encontrados'
            }), 400
        
        polygons_data = []
        for p in polygons:
            geojson = json.loads(p.geojson_data)
            # Extrai coordenadas do GeoJSON (geometry.coordinates[0])
            # GeoJSON format: {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[lon, lat], ...]]}}
            coords = []
            if isinstance(geojson, dict):
                geometry = geojson.get('geometry', {})
                if geometry:
                    coords_raw = geometry.get('coordinates', [])
                    if coords_raw and len(coords_raw) > 0:
                        # coords_raw[0] é o anel externo do polígono
                        # Formato GeoJSON: [lon, lat], converter para [lat, lon]
                        coords = [[c[1], c[0]] for c in coords_raw[0]]
            
            print(f"🔍 Polígono {p.group_name} (ID: {p.id}): {len(coords)} coordenadas extraídas")
            
            polygons_data.append({
                'id': p.id,
                'name': p.group_name,
                'coordinates': coords
            })
        
        print(f"📊 Total de polígonos preparados: {len(polygons_data)}")
        
        # Executa K-Means com filtro de polígonos (usando KMM para filtrar)
        from ml.KMM import run_kmeans_clustering
        
        df_result, num_clusters, clients_count = run_kmeans_clustering(
            df_clientes,
            dias,
            selected_polygon_ids=grupos_selecionados,
            polygons_data=polygons_data
        )
        
        if df_result.empty:
            return jsonify({
                'success': False,
                'error': 'Nenhum cliente encontrado nas áreas selecionadas'
            }, 400)
        
        # Converte DataFrame filtrado para formato do route_optimizer
        from ml.route_optimizer import convert_kmm_to_optimizer_format, create_routes_knn, format_result_for_api
        
        filtered_clients = convert_kmm_to_optimizer_format(df_result)
        
        print(f"🎯 Iniciando route_optimizer: {len(filtered_clients)} clientes, {dias} dias, limite: {max_clients_per_day}")
        
        # Aplica algoritmo de roteirização com filtro de tamanho
        groups = create_routes_knn(
            filtered_clients,
            n_days=dias,
            max_clients_per_day=max_clients_per_day
        )
        
        if not groups:
            return jsonify({
                'success': False,
                'error': 'Erro ao criar grupos de roteirização'
            }), 500
        
        # Busca scores dos clientes para incluir no resultado
        scores_map = {}
        try:
            client_scores = ClientScore.query.filter_by(user_id=uid).all()
            for score in client_scores:
                scores_map[score.hash_cliente] = {
                    'score_total': score.score_total,
                    'segmento': score.get_segmento() if hasattr(score, 'get_segmento') else None
                }
        except Exception as e:
            logger.warning(f"Erro ao buscar scores: {e}")
        
        # Cria mapeamento de polígonos (id -> nome)
        polygons_map = {p['id']: p['name'] for p in polygons_data}
        
        # Formata resultado para API
        result = format_result_for_api(groups, scores_map, polygons_map)
        
        # Adiciona informações extras
        result['clients_count_by_polygon'] = clients_count
        result['requested_days'] = dias
        result['max_clients_per_day'] = max_clients_per_day
        
        # Mensagem descritiva
        if result['split_groups'] > 0:
            result['message'] = f"{result['total_groups']} grupos criados para {dias} dias! ({result['split_groups']} grupos foram divididos pelo filtro de tamanho)"
        else:
            result['message'] = f"{result['total_groups']} grupos criados para {dias} dias!"
        
        print(f"✅ Roteirização concluída: {result['total_groups']} grupos ({result['split_groups']} divididos)")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Erro ao processar roteirização: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500


# ============================================================================
# ENDPOINTS DE API - SCORES RFM
# ============================================================================

@main.route('/autenticado/scores/estatisticas')
def scores_estatisticas():
    """
    API JSON: Estatísticas agregadas de scores RFM do usuário
    
    Retorna:
    --------
    {
        "total_clientes": int,
        "score_medio": float,
        "score_mediano": float,
        "distribuicao": {"VIP": int, "Alto Valor": int, ...},
        "ultima_atualizacao": ISO datetime
    }
    """
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        from ml.client_scoring import obter_estatisticas_scores
        
        stats = obter_estatisticas_scores(int(user_id))
        
        if stats is None:
            return jsonify({
                'message': 'Nenhum score calculado ainda',
                'action': 'Importe histórico de vendas primeiro',
                'endpoint_upload': url_for('main.historicovendas')
            }), 404
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de scores: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@main.route('/autenticado/scores/segmento/<segmento>')
def scores_por_segmento(segmento):
    """
    API JSON: Lista clientes de um segmento específico
    
    Parâmetros:
    -----------
    segmento : str (URL param)
        'VIP', 'Alto Valor', 'Médio' ou 'Em Risco'
    
    Query params:
    - limit: int (default 50) - Máximo de clientes retornados
    
    Retorna:
    --------
    {
        "segmento": str,
        "total": int,
        "clientes": [
            {
                "hash_cliente": str,
                "score_total": float,
                "score_recencia": float,
                "frequencia": int,
                "valor_total": float,
                ...
            }
        ]
    }
    """
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Validar segmento
    segmentos_validos = ['VIP', 'Alto Valor', 'Médio', 'Em Risco']
    if segmento not in segmentos_validos:
        return jsonify({
            'error': f'Segmento inválido',
            'segmentos_validos': segmentos_validos,
            'recebido': segmento
        }), 400
    
    try:
        from ml.client_scoring import obter_clientes_segmento
        
        # Obter limite da query string
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # Máximo absoluto de 200
        
        clientes = obter_clientes_segmento(int(user_id), segmento)
        
        return jsonify({
            'segmento': segmento,
            'total': len(clientes),
            'retornados': min(len(clientes), limit),
            'clientes': [c.to_dict() for c in clientes[:limit]]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar segmento '{segmento}': {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@main.route('/autenticado/scores/recalcular', methods=['POST'])
def scores_recalcular():
    """
    Endpoint para forçar recálculo de scores RFM
    
    Útil quando:
    - Usuário importou mais vendas manualmente no banco
    - Houve update no histórico de vendas
    - Quer testar novos pesos RFM
    
    Body (JSON opcional):
    {
        "pesos": {
            "recencia": 0.30,
            "frequencia": 0.25,
            "monetario": 0.25,
            "satisfacao": 0.20
        }
    }
    """
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        # Obter pesos customizados (se enviados)
        pesos = None
        if request.is_json:
            data = request.get_json()
            pesos = data.get('pesos')
            
            # Validar pesos
            if pesos:
                soma = sum(pesos.values())
                if not (0.99 <= soma <= 1.01):  # Tolerância para float
                    return jsonify({
                        'error': 'Pesos devem somar 1.0',
                        'soma_atual': soma
                    }), 400
        
        from ml.client_scoring import calcular_scores_para_usuario
        
        logger.info(f"🔄 Recálculo manual de scores solicitado | user_id={user_id} | pesos={pesos}")
        
        resultado = calcular_scores_para_usuario(
            user_id=int(user_id),
            pesos=pesos,
            forcar_recalculo=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Scores recalculados com sucesso',
            'resultado': resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao recalcular scores: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ENDPOINTS DE API - CALENDÁRIOS SALVOS
# ============================================================================

@main.route('/autenticado/roteirizacao/salvar-calendario', methods=['POST'])
@login_required
def salvar_calendario():
    """
    API JSON: Salva um calendário de roteirização
    
    Payload esperado:
    {
        "nome": str,
        "data_criacao": ISO datetime,
        "configuracao": {
            "dias": int,
            "incluir_sabado": bool,
            "incluir_domingo": bool,
            "max_clientes_dia": int
        },
        "alocacoes": [
            {
                "dia": int,
                "cluster_id": int,
                "num_clientes": int,
                "score_medio": float,
                "polygon_name": str
            }
        ],
        "total_clusters": int,
        "total_clientes": int
    }
    """
    try:
        from base.models import SavedCalendar
        import json
        
        print('\n📥 [SALVAR CALENDÁRIO] Recebendo requisição...')
        
        data = request.get_json()
        print(f'📦 Dados recebidos: {len(str(data))} caracteres')
        print(f'📝 Nome: {data.get("nome") if data else "SEM DADOS"}')
        print(f'📊 Alocações: {len(data.get("alocacoes", [])) if data else 0}')
        print(f'👤 User ID: {current_user.id}')
        
        # Validação básica
        if not data or not data.get('nome'):
            print('❌ Erro: Nome não fornecido')
            return jsonify({
                'success': False,
                'error': 'Nome do calendário é obrigatório'
            }), 400
        
        if not data.get('alocacoes') or len(data['alocacoes']) == 0:
            print('❌ Erro: Sem alocações')
            return jsonify({
                'success': False,
                'error': 'Calendário deve ter ao menos uma alocação'
            }), 400
        
        # Debug: Verifica se as alocações têm clientes
        alocacoes = data.get('alocacoes', [])
        for i, aloc in enumerate(alocacoes[:3]):  # Primeiras 3 alocações
            num_clientes = len(aloc.get('clientes', []))
            print(f'  Dia {aloc.get("dia")}: {num_clientes} clientes no array')
        
        # Cria novo calendário
        print('💾 Criando objeto SavedCalendar...')
        calendario = SavedCalendar(
            user_id=current_user.id,
            nome=data['nome'],
            descricao=data.get('descricao'),
            configuracao=json.dumps(data.get('configuracao', {})),
            alocacoes=json.dumps(data.get('alocacoes', [])),
            total_clusters=data.get('total_clusters', 0),
            total_clientes=data.get('total_clientes', 0)
        )
        
        print('💾 Salvando no banco de dados...')
        db.session.add(calendario)
        db.session.commit()
        
        print(f'✅ Calendário salvo com ID: {calendario.id}')
        logger.info(f"Calendário '{data['nome']}' salvo pelo usuário {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Calendário salvo com sucesso',
            'id': calendario.id,
            'calendario': calendario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'❌ ERRO ao salvar calendário: {str(e)}')
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao salvar calendário: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erro ao salvar: {str(e)}'
        }), 500


@main.route('/autenticado/roteirizacao/calendarios')
@login_required
def listar_calendarios():
    """
    API JSON: Lista todos os calendários salvos do usuário
    """
    try:
        from base.models import SavedCalendar
        
        calendarios = SavedCalendar.query.filter_by(
            user_id=current_user.id
        ).order_by(SavedCalendar.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'calendarios': [c.to_dict() for c in calendarios]
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar calendários: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/autenticado/roteirizacao/calendario/<int:id>')
@login_required
def obter_calendario(id):
    """
    API JSON: Obtém um calendário específico
    """
    try:
        from base.models import SavedCalendar
        
        calendario = SavedCalendar.query.filter_by(
            id=id,
            user_id=current_user.id
        ).first()
        
        if not calendario:
            return jsonify({
                'success': False,
                'error': 'Calendário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'calendario': calendario.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter calendário: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/autenticado/roteirizacao/calendario/<int:calendario_id>/clientes/<int:dia>')
@login_required
def obter_clientes_cluster_dia(calendario_id, dia):
    """
    API JSON: Obtém lista de clientes de um cluster específico em um dia do calendário
    
    Retorna informações detalhadas dos clientes incluindo:
    - hash_cliente
    - nome (se disponível no banco client_name)
    - latitude/longitude
    - score
    - cidade/estado
    """
    try:
        from base.models import SavedCalendar
        import json
        
        # Busca o calendário
        calendario = SavedCalendar.query.filter_by(
            id=calendario_id,
            user_id=current_user.id
        ).first()
        
        if not calendario:
            return jsonify({
                'success': False,
                'error': 'Calendário não encontrado'
            }), 404
        
        # Parse das alocações
        alocacoes = json.loads(calendario.alocacoes) if calendario.alocacoes else []
        
        # Encontra a alocação do dia específico
        alocacao_dia = next((a for a in alocacoes if a['dia'] == dia), None)
        
        if not alocacao_dia:
            return jsonify({
                'success': False,
                'error': f'Nenhum cluster alocado para o dia {dia}'
            }), 404
        
        # Busca informações detalhadas dos clientes
        clientes_detalhados = []
        for cliente in alocacao_dia.get('clientes', []):
            hash_cliente = cliente.get('hash_cliente')
            
            # Busca nome do cliente no banco client_name
            cliente_db = ClientName.query.filter_by(hash_client=hash_cliente).first()
            
            cliente_info = {
                'hash_cliente': hash_cliente,
                'nome': cliente_db.name_client if cliente_db else 'Desconhecido',
                'cidade': cliente_db.cidade if cliente_db else None,
                'estado': cliente_db.estado if cliente_db else None,
                'latitude': cliente.get('latitude'),
                'longitude': cliente.get('longitude'),
                'score': cliente.get('score')
            }
            
            clientes_detalhados.append(cliente_info)
        
        return jsonify({
            'success': True,
            'dia': dia,
            'cluster_id': alocacao_dia.get('cluster_id'),
            'polygon_name': alocacao_dia.get('polygon_name'),
            'num_clientes': len(clientes_detalhados),
            'score_medio': alocacao_dia.get('score_medio'),
            'clientes': clientes_detalhados
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter clientes do cluster: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/autenticado/painel/pontos-saida')
@login_required
def listar_pontos_saida():
    """
    API: Lista todos os pontos de saída (user_point=True) do usuário
    
    Retorna JSON com id, nome, latitude, longitude
    Usado no seletor de pontos de saída do painel de rotas
    """
    try:
        from base.models import LatLong
        
        # Busca pontos de saída do usuário (campo correto é id_user, não user_id)
        pontos = LatLong.query.filter_by(
            id_user=current_user.id,
            user_point=True
        ).all()
        
        if not pontos:
            return jsonify({
                'success': True,
                'pontos': [],
                'message': 'Nenhum ponto de saída cadastrado'
            })
        
        # Formata dados
        pontos_list = []
        for ponto in pontos:
            pontos_list.append({
                'id': ponto.id,
                'hash_client': ponto.hash_client,
                'nome': ponto.hash_client,  # Pode ser melhorado com campo nome no futuro
                'latitude': float(ponto.latitude) if ponto.latitude else None,
                'longitude': float(ponto.longitude) if ponto.longitude else None
            })
        
        return jsonify({
            'success': True,
            'pontos': pontos_list
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar pontos de saída: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/autenticado/roteirizacao/calendario/<int:calendario_id>/exportar-clientes')
@login_required
def exportar_clientes_calendario(calendario_id):
    """
    API JSON: Exporta todos os clientes do calendário organizados por dia
    
    Útil para gerar relatórios, planilhas ou visualizações detalhadas
    """
    try:
        from base.models import SavedCalendar
        import json
        
        # Busca o calendário
        calendario = SavedCalendar.query.filter_by(
            id=calendario_id,
            user_id=current_user.id
        ).first()
        
        if not calendario:
            return jsonify({
                'success': False,
                'error': 'Calendário não encontrado'
            }), 404
        
        # Parse das alocações
        alocacoes = json.loads(calendario.alocacoes) if calendario.alocacoes else []
        
        # Organiza todos os clientes por dia
        resultado = {
            'calendario_id': calendario_id,
            'nome_calendario': calendario.nome,
            'created_at': calendario.created_at.isoformat() if calendario.created_at else None,
            'dias': []
        }
        
        for alocacao in alocacoes:
            dia_info = {
                'dia': alocacao['dia'],
                'cluster_id': alocacao['cluster_id'],
                'polygon_name': alocacao.get('polygon_name'),
                'num_clientes': alocacao.get('num_clientes', 0),
                'score_medio': alocacao.get('score_medio'),
                'clientes': []
            }
            
            # Busca informações detalhadas de cada cliente
            for cliente in alocacao.get('clientes', []):
                hash_cliente = cliente.get('hash_cliente')
                cliente_db = ClientName.query.filter_by(hash_client=hash_cliente).first()
                
                # Garante conversão de coordenadas para float
                try:
                    lat = float(cliente.get('latitude')) if cliente.get('latitude') else None
                    lng = float(cliente.get('longitude')) if cliente.get('longitude') else None
                except (TypeError, ValueError):
                    lat = None
                    lng = None
                
                dia_info['clientes'].append({
                    'hash_cliente': hash_cliente,
                    'nome': cliente_db.name_client if cliente_db else 'Desconhecido',
                    'cidade': cliente_db.cidade if cliente_db else 'N/A',
                    'estado': cliente_db.estado if cliente_db else 'N/A',
                    'latitude': lat,
                    'longitude': lng,
                    'score': float(cliente.get('score')) if cliente.get('score') else None
                })
            
            resultado['dias'].append(dia_info)
        
        return jsonify({
            'success': True,
            'calendario_id': resultado['calendario_id'],
            'nome_calendario': resultado['nome_calendario'],
            'created_at': resultado['created_at'],
            'dias': resultado['dias']
        })
        
    except Exception as e:
        logger.error(f"Erro ao exportar clientes: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/autenticado/roteirizacao/calendario/<int:id>', methods=['DELETE'])
@login_required
def deletar_calendario(id):
    """
    API JSON: Deleta um calendário salvo
    """
    try:
        from base.models import SavedCalendar
        
        calendario = SavedCalendar.query.filter_by(
            id=id,
            user_id=current_user.id
        ).first()
        
        if not calendario:
            return jsonify({
                'success': False,
                'error': 'Calendário não encontrado'
            }), 404
        
        nome = calendario.nome
        db.session.delete(calendario)
        db.session.commit()
        
        logger.info(f"Calendário '{nome}' (ID:{id}) deletado pelo usuário {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': f'Calendário "{nome}" deletado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar calendário: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/autenticado/painel/ponto-saida', methods=['GET'])
@login_required
def obter_ponto_saida():
    """
    API JSON: Retorna o ponto de saída (base) do usuário atual
    """
    try:
        from base.models import LatLong
        
        logger.info(f"Buscando ponto de saída para user_id: {current_user.id}")
        
        # Busca o ponto marcado como user_point=True
        ponto_base = LatLong.query.filter_by(
            id_user=current_user.id,
            user_point=True
        ).first()
        
        if not ponto_base:
            logger.warning(f"Ponto de saída não encontrado para user_id: {current_user.id}")
            return jsonify({
                'success': False,
                'error': 'Ponto de saída não configurado. Configure em Pontos de Saída.'
            }), 404
        
        # Garante conversão para float
        try:
            lat = float(ponto_base.latitude)
            lng = float(ponto_base.longitude)
        except (TypeError, ValueError) as e:
            logger.error(f"Coordenadas inválidas: lat={ponto_base.latitude}, lng={ponto_base.longitude}")
            return jsonify({
                'success': False,
                'error': 'Coordenadas do ponto de saída inválidas'
            }), 500
        
        logger.info(f"Ponto de saída encontrado: lat={lat}, lng={lng}")
        
        return jsonify({
            'success': True,
            'ponto_saida': {
                'latitude': lat,
                'longitude': lng,
                'hash': ponto_base.hash_client,
                'nome': 'Base/Saída'
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar ponto de saída: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
