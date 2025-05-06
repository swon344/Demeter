// Admin Panel JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Alert auto-dismiss
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm delete actions
    document.querySelectorAll('.confirm-delete').forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Bu öğeyi silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
                e.preventDefault();
            }
        });
    });

    // Scientific name preview for seeds
    var genusSelect = document.getElementById('genus_id');
    var speciesInput = document.getElementById('species_name');
    var scientificPreview = document.getElementById('scientific-preview');

    if (genusSelect && speciesInput && scientificPreview) {
        function updateScientificName() {
            var genusOption = genusSelect.options[genusSelect.selectedIndex];
            var genusName = genusOption.text;
            var speciesName = speciesInput.value;

            if (genusName && genusName !== 'Cins Seçin' && speciesName) {
                scientificPreview.textContent = genusName + ' ' + speciesName;
            } else {
                scientificPreview.textContent = 'Bilimsel adı görmek için cins ve tür adı girin';
            }
        }

        genusSelect.addEventListener('change', updateScientificName);
        speciesInput.addEventListener('input', updateScientificName);

        // Initial update
        updateScientificName();
    }

    // Trait selection counter
    var traitCheckboxes = document.querySelectorAll('input[name="traits"]');
    var traitCounter = document.getElementById('trait-counter');

    if (traitCheckboxes.length > 0 && traitCounter) {
        function updateTraitCounter() {
            var selectedCount = document.querySelectorAll('input[name="traits"]:checked').length;
            traitCounter.textContent = selectedCount + ' özellik seçildi';
        }

        traitCheckboxes.forEach(function(checkbox) {
            checkbox.addEventListener('change', updateTraitCounter);
        });

        // Initial update
        updateTraitCounter();
    }

    // Search functionality
    var searchInput = document.getElementById('search-input');
    var searchTarget = document.getElementById('search-target');

    if (searchInput && searchTarget) {
        searchInput.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var items = searchTarget.querySelectorAll('.searchable-item');

            items.forEach(function(item) {
                var text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});