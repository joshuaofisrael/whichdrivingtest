(function () {
  var sel = document.getElementById("state-jump");
  if (sel) {
    sel.addEventListener("change", function () {
      if (sel.value) location.href = sel.value;
    });
  }
  var q = document.getElementById("state-filter");
  if (q) {
    q.addEventListener("input", function () {
      var n = q.value.trim().toLowerCase();
      document.querySelectorAll("[data-state]").forEach(function (el) {
        var name = (el.getAttribute("data-state") || "").toLowerCase();
        el.hidden = !!(n && name.indexOf(n) === -1);
      });
    });
  }
})();
