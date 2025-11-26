import json
import numpy as np
from shapely.geometry import Point, Polygon as ShapelyPolygon
from shapely.prepared import prep
from functools import lru_cache


class GeoUtils:    
    @staticmethod
    def point_in_polygon_fast(lat, lon, polygon_coords):
        """
        Verifica se um ponto está dentro de um polígono usando Shapely (muito mais rápido)
        
        Args:
            lat (float): Latitude do ponto
            lon (float): Longitude do ponto
            polygon_coords (list): Lista de coordenadas [[lat1, lon1], [lat2, lon2], ...]
        
        Returns:
            bool: True se o ponto está dentro do polígono
        """
        try:
            # Shapely espera Point(longitude, latitude)
            point = Point(lon, lat)
            # polygon_coords são [lat, lng], então invertemos para (lng, lat)
            polygon = ShapelyPolygon([(coord[1], coord[0]) for coord in polygon_coords])
            return polygon.contains(point)
        except Exception as e:
            print(f"Erro ao verificar ponto no polígono: {e}")
            return False
    
    @staticmethod
    def get_prepared_polygon(polygon_coords):
        """
        Cria um polígono preparado (otimizado) para múltiplas verificações
        
        Args:
            polygon_coords (list): Lista de coordenadas [[lat1, lon1], [lat2, lon2], ...]
        
        Returns:
            PreparedGeometry: Polígono otimizado para verificações rápidas
        """
        try:
            # Shapely espera (lng, lat), coords são [lat, lng]
            polygon = ShapelyPolygon([(coord[1], coord[0]) for coord in polygon_coords])
            return prep(polygon)
        except Exception as e:
            print(f"Erro ao criar polígono preparado: {e}")
            return None
    
    @staticmethod
    def filter_clients_by_polygons(clients, polygons):
        """
        Filtra clientes por múltiplos polígonos de forma otimizada
        
        Args:
            clients (list): Lista de dicts com {id, latitude, longitude, ...}
            polygons (list): Lista de dicts com {id, name, coordinates, ...}
        
        Returns:
            dict: {polygon_id: [lista de clientes], ...}
        """
        result = {poly['id']: [] for poly in polygons}
        
        # Prepara todos os polígonos uma vez (otimização)
        prepared_polygons = {}
        for poly in polygons:
            coords = poly.get('coordinates', [])
            if coords:
                prepared = GeoUtils.get_prepared_polygon(coords)
                if prepared:
                    # Shapely espera (lng, lat), coords são [lat, lng]
                    raw_polygon = ShapelyPolygon([(c[1], c[0]) for c in coords])
                    prepared_polygons[poly['id']] = {
                        'geometry': prepared,
                        'raw_polygon': raw_polygon
                    }
        
        # Verifica cada cliente contra todos os polígonos preparados
        for client in clients:
            lat = client.get('latitude')
            lon = client.get('longitude')
            
            if lat is None or lon is None:
                continue
            
            # Shapely espera Point(longitude, latitude)
            point = Point(lon, lat)
            
            for poly_id, poly_data in prepared_polygons.items():
                try:
                    if poly_data['geometry'].contains(point):
                        result[poly_id].append(client)
                except Exception as e:
                    # Fallback para polígono não preparado
                    if poly_data['raw_polygon'].contains(point):
                        result[poly_id].append(client)
        
        return result
    
    @staticmethod
    def calculate_bbox(polygon_coords):
        """
        Calcula o bounding box (retângulo envolvente) de um polígono
        Útil para pré-filtrar pontos antes da verificação precisa
        
        Args:
            polygon_coords (list): Lista de coordenadas [[lat1, lon1], [lat2, lon2], ...]
        
        Returns:
            dict: {min_lat, max_lat, min_lon, max_lon}
        """
        if not polygon_coords:
            return None
        
        lats = [coord[0] for coord in polygon_coords]
        lons = [coord[1] for coord in polygon_coords]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons)
        }
    
    @staticmethod
    def point_in_bbox(lat, lon, bbox):
        """
        Verifica rapidamente se um ponto está dentro do bounding box
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            bbox (dict): Bounding box {min_lat, max_lat, min_lon, max_lon}
        
        Returns:
            bool: True se está dentro do bbox
        """
        return (bbox['min_lat'] <= lat <= bbox['max_lat'] and
                bbox['min_lon'] <= lon <= bbox['max_lon'])
    
    @staticmethod
    def filter_clients_by_polygons_optimized(clients, polygons):
        """
        Versão otimizada com bounding box pré-filtro
        Reduz drasticamente o número de verificações precisas
        
        Args:
            clients (list): Lista de clientes com {latitude, longitude, ...}
            polygons (list): Lista de polígonos com {coordinates: [[lat, lng], ...], ...}
        
        Returns:
            dict: {polygon_id: [clientes], ...}
        """
        result = {poly['id']: [] for poly in polygons}
        
        # Prepara polígonos e calcula bounding boxes
        polygon_data = {}
        for poly in polygons:
            coords = poly.get('coordinates', [])
            if not coords:
                continue
            
            # Validação: garante que coords é uma lista de listas com 2 elementos numéricos
            try:
                # Filtra apenas coordenadas válidas
                valid_coords = []
                for c in coords:
                    if isinstance(c, (list, tuple)) and len(c) >= 2:
                        try:
                            lat = float(c[0])
                            lon = float(c[1])
                            valid_coords.append([lat, lon])
                        except (ValueError, TypeError):
                            continue
                
                if len(valid_coords) < 3:
                    print(f"⚠️ Polígono {poly.get('id')} tem menos de 3 coordenadas válidas")
                    continue
                
                bbox = GeoUtils.calculate_bbox(valid_coords)
                # Shapely espera (longitude, latitude), mas coords são [lat, lng]
                # Então invertemos: c[1] é lng, c[0] é lat
                shapely_poly = ShapelyPolygon([(c[1], c[0]) for c in valid_coords])
                prepared_poly = prep(shapely_poly)
                
                polygon_data[poly['id']] = {
                    'bbox': bbox,
                    'geometry': prepared_poly,
                    'raw': shapely_poly
                }
            except Exception as e:
                print(f"❌ Erro ao processar polígono {poly.get('id')}: {e}")
                continue
        
        # Filtra clientes usando bounding box primeiro (muito rápido)
        # Depois verifica com polígono preciso apenas os candidatos
        for client in clients:
            lat = client.get('latitude')
            lon = client.get('longitude')
            
            if lat is None or lon is None:
                continue
            
            # Shapely espera Point(longitude, latitude)
            point = Point(lon, lat)
            
            for poly_id, pdata in polygon_data.items():
                if not GeoUtils.point_in_bbox(lat, lon, pdata['bbox']):
                    continue
                try:
                    if pdata['geometry'].contains(point):
                        result[poly_id].append(client)
                except Exception:
                    if pdata['raw'].contains(point):
                        result[poly_id].append(client)
        
        return result


def batch_assign_clients_to_polygons(clients_data, polygons_data):
    """
    Função auxiliar para processar em lote a atribuição de clientes a polígonos
    
    Args:
        clients_data (list): Lista de clientes do banco
        polygons_data (list): Lista de polígonos do banco
    
    Returns:
        list: Lista de dicts {client_id, polygon_id} para inserir na tabela KNN
    """
    assignments = []
    
    result = GeoUtils.filter_clients_by_polygons_optimized(clients_data, polygons_data)
    for polygon_id, clients in result.items():
        for client in clients:
            assignments.append({
                'client_id': client.get('id'),
                'polygon_id': polygon_id,
                'client_hash': client.get('hash_client')
            })
    
    return assignments
