// ...existing code...
(function(){
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    if (!sidebar || !toggleBtn) return;

    const STORAGE_KEY = 'synapselog_sidebar_open';

    function setSidebarOpen(open) {
        if (open) {
            sidebar.classList.add('open');
            toggleBtn.setAttribute('aria-pressed', 'true');
            toggleBtn.setAttribute('aria-expanded', 'true');
            localStorage.setItem(STORAGE_KEY, '1');
        } else {
            sidebar.classList.remove('open');
            toggleBtn.setAttribute('aria-pressed', 'false');
            toggleBtn.setAttribute('aria-expanded', 'false');
            localStorage.setItem(STORAGE_KEY, '0');
        }
    }

    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === '1') setSidebarOpen(true);
    else {
        if (window.innerWidth >= 900) setSidebarOpen(true);
        else setSidebarOpen(false);
    }

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        setSidebarOpen(!sidebar.classList.contains('open'));
    });

    document.addEventListener('click', (e) => {
        if (window.innerWidth >= 900) return;
        if (!sidebar.classList.contains('open')) return;
        if (sidebar.contains(e.target) || toggleBtn.contains(e.target)) return;
        setSidebarOpen(false);
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) setSidebarOpen(false);
    });

    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (window.innerWidth >= 900 && localStorage.getItem(STORAGE_KEY) !== '0') {
                setSidebarOpen(true);
            }
        }, 150);
    });
})();