// This script launches the Copy Detail modal.
// n.b. that it requires Bootstrap 5.

$(function () {

  // Option A: click-triggered modal launch
  document.body.addEventListener("click", function (event) {
    const trigger = event.target.closest("[data-form]");
    if (!trigger) return;

    event.preventDefault();
    const fetchUrl = trigger.getAttribute("data-form");
    if (!fetchUrl) return;

    fetch(fetchUrl)
      .then((response) => response.text())
      .then((html) => {
        const container = document.getElementById("copyModal");
        if (!container) {
          console.error("Modal container #copyModal not found");
          return;
        }

        container.innerHTML = html;

        const modalElem = container.querySelector(".modal-dialog")?.parentNode || container;

        if (modalElem) {
          console.log("Modal initialized from click, attempting to show...");
          const myModal = new bootstrap.Modal(modalElem);
          setTimeout(() => myModal.show(), 10);
        } else {
          console.error("Modal dialog element not found in loaded HTML");
        }
      });
  });

  // Option B: modal launch from a direct link
  if (typeof window.open_modal_id !== "undefined") {
    const openId = window.open_modal_id;
 
    const trigger = document.querySelector('[data-form*="/' + openId + '/"]');

    if (trigger) {
      console.log("Found trigger for modal:", trigger);
      trigger.click();
    } else {
      console.log("No trigger found for modal; fetching directly.");
      fetch(`/copy/${openId}/`)
        .then((response) => response.text())
        .then((html) => {
          const container = document.getElementById("copyModal");
          if (!container) {
            console.error("Modal container #copyModal not found");
            return;
          }

          container.innerHTML = html;

          const modalElem = container.querySelector(".modal-dialog")?.parentNode || container;

          if (modalElem) {
            console.log("Modal initialized from open_modal_id, attempting to show...");
            const myModal = new bootstrap.Modal(modalElem);
            setTimeout(() => myModal.show(), 10);
          } else {
            console.error("Modal dialog element not found in loaded HTML");
          }
        });
    }
  }
});
