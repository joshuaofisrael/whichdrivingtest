(function () {
  var KEY = "wdt-consent";
  var script = document.querySelector("script[data-ga4-loader]");
  var banner = document.getElementById("consent-banner");
  var accept = document.getElementById("consent-accept");
  var reject = document.getElementById("consent-reject");
  var settings = document.getElementById("cookie-settings");
  var loaded = false;

  function read() {
    try {
      return localStorage.getItem(KEY) || "";
    } catch (err) {
      return "";
    }
  }

  function write(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (err) {}
  }

  function show() {
    if (banner) banner.hidden = false;
  }

  function hide() {
    if (banner) banner.hidden = true;
  }

  function deny() {
    if (typeof gtag === "function") {
      gtag("consent", "update", {
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
        analytics_storage: "denied"
      });
    }
  }

  function loadGA4() {
    if (loaded || !script || typeof gtag !== "function") return;
    var id = script.getAttribute("data-ga4-id") || "";
    var loader = script.getAttribute("data-ga4-loader") || "https://www.googletagmanager.com/gtag/js";
    if (!/^G-[A-Z0-9]+$/.test(id)) return;
    loaded = true;
    gtag("consent", "update", { analytics_storage: "granted" });
    var tag = document.createElement("script");
    tag.async = true;
    tag.src = loader + "?id=" + encodeURIComponent(id);
    document.head.appendChild(tag);
    gtag("js", new Date());
    gtag("config", id);
  }

  if (accept) {
    accept.addEventListener("click", function () {
      write("granted");
      loadGA4();
      hide();
    });
  }
  if (reject) {
    reject.addEventListener("click", function () {
      write("denied");
      deny();
      hide();
    });
  }
  if (settings) {
    settings.addEventListener("click", function (event) {
      event.preventDefault();
      show();
    });
  }

  var choice = read();
  if (choice === "granted") {
    loadGA4();
    hide();
  } else if (choice === "denied") {
    deny();
    hide();
  } else {
    show();
  }
})();
