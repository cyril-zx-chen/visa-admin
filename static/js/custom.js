document.addEventListener('DOMContentLoaded', function () {
  // Bootstrap tooltip initialisation
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // Student list search filter
  var searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('keyup', function () {
      var term = this.value.toLowerCase();
      document.querySelectorAll('#studentTable tbody tr').forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
      });
    });
  }

  // Delete confirmation for buttons with data-confirm attribute
  document.querySelectorAll('button[data-confirm], input[type="submit"][data-confirm]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });
});
