// This script handles the search bar's appearance and autocomplete functions

document.addEventListener("DOMContentLoaded", function () {
  // Toggle search bar visibility
  const searchButton = document.getElementById("site-search-button");
  const searchBarBlock = document.getElementById("search-bar-block");

  if (searchButton && searchBarBlock) {
    searchButton.addEventListener("click", function (e) {
      e.preventDefault();
      searchBarBlock.classList.toggle("search-bar-hidden");
    });
  }

  // Initialize autocomplete
  $(function () {
    var autofillMap = {
      location: '/autofill/location/',
      geography: '/autofill/geography/',
      provenance_name: '/autofill/provenance/',
      collection: '/autofill/collection/'
    };

    var autofillResponse = function (field, query, response) {
      fetch(autofillMap[field] + query + '/')
        .then((matches) => matches.json())
        .then((matches_json) => response(matches_json.matches));
    };

    $('#search-bar-form-text').autocomplete({
      minLength: 3,
      source: function (request, response) {
        var field = $('#search-bar-form-field').val();
        if (autofillMap.hasOwnProperty(field)) {
          autofillResponse(field, request.term, response);
        }
      },
      select: function (evt, ui) {
        $('#search-bar-form-text').val(ui.item.value);
        $('#search-bar-form').submit();
      }
    });

    $('#search-bar-form-field').change(function () {
      if ($('#search-bar-form-field option:selected').val() === 'collection') {
        $('#search-bar-form-text').autocomplete('search', '   ');
      }
    });
  });
});
