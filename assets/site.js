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
  document.querySelectorAll("table.sortable").forEach(function (table) {
    table.querySelectorAll("thead th button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tbody = table.querySelector("tbody");
        var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
        var dir = btn.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        table.querySelectorAll("thead th button").forEach(function (other) {
          other.setAttribute("aria-sort", "none");
        });
        btn.setAttribute("aria-sort", dir);
        var key = btn.getAttribute("data-sort");
        rows.sort(function (a, b) {
          var av = a.getAttribute(key) || "";
          var bv = b.getAttribute(key) || "";
          var an = parseFloat(av);
          var bn = parseFloat(bv);
          var cmp;
          if (av === "" && bv === "") cmp = 0;
          else if (av === "") cmp = 1;
          else if (bv === "") cmp = -1;
          else if (!isNaN(an) && !isNaN(bn)) cmp = an - bn;
          else cmp = av.localeCompare(bv);
          return dir === "ascending" ? cmp : -cmp;
        });
        rows.forEach(function (row) {
          tbody.appendChild(row);
        });
      });
    });
  });
})();
