// ...existing code...
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  toggle?.addEventListener('click', () => sidebar.classList.toggle('open'));
});
// ...existing code...