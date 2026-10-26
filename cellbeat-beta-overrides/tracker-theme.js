/* Appearance and compact beta utility layout. Song state/playback are untouched. */
(function (root) {
  "use strict";
  var sheet = document.getElementById("trackerTheme");
  var select = document.getElementById("themeSelect");
  var key = "cellbeat-mini:theme", theme = "compact";

  try { if (root.localStorage.getItem(key) === "classic") theme = "classic"; } catch (error) {}

  function apply(value) {
    theme = value === "classic" ? "classic" : "compact";
    if (sheet) sheet.disabled = theme === "classic";
    if (select) select.value = theme;
    document.documentElement.setAttribute("data-theme", theme);
  }

  apply(theme);
  if (select) select.addEventListener("change", function () {
    apply(select.value);
    try { root.localStorage.setItem(key, theme); } catch (error) {}
  });

  function compactStyle() {
    if (document.getElementById("cellbeatCompactUtilities")) return;
    var style = document.createElement("style");
    style.id = "cellbeatCompactUtilities";
    style.textContent =
      ".compact-utility,.compact-help{border:0!important;border-top:1px solid #46535d!important;box-shadow:none!important;background:transparent!important;padding:0!important;margin:0!important}" +
      ".compact-utility>summary,.compact-help>summary{min-height:38px!important;margin:0!important;padding:8px 2px!important;display:flex!important;align-items:center;gap:7px;font-size:13px!important;line-height:1.2!important;font-weight:700;text-transform:none!important;letter-spacing:0!important;cursor:pointer;background:transparent!important;border:0!important}" +
      ".compact-utility[open]>summary,.compact-help[open]>summary{border-bottom:1px solid #38444d!important}" +
      ".compact-utility-body,.compact-copy{padding:4px 2px 8px!important;font-size:12px!important;line-height:1.4!important}" +
      ".compact-utility .message,.compact-copy,.compact-utility .help{font-size:12px!important;line-height:1.4!important;margin:4px 0!important;color:var(--muted)!important}" +
      ".compact-utility .actions{display:flex!important;gap:4px!important;flex-wrap:wrap!important}" +
      ".compact-utility .btn,.compact-utility select,.compact-utility input{font-size:12px!important}" +
      ".compact-utility .btn{min-height:40px!important;padding:5px 8px!important}" +
      ".beta-recordings.compact-utility>summary{background:transparent!important;padding:8px 2px!important;min-height:38px!important}" +
      ".beta-recordings .beta-recording-body{padding:4px 2px 8px!important}" +
      ".beta-recording-row label,.beta-recording-name,.beta-recording-help{font-size:12px!important;line-height:1.35!important}" +
      "#advanced.compact-utility{margin-top:3px!important}" +
      "#advanced.compact-utility>.panel{border:0!important;border-top:1px solid #38444d!important;box-shadow:none!important;background:transparent!important;margin:0!important;padding:6px 2px!important}" +
      "#advanced.compact-utility>.panel h2{font-size:12px!important;padding:3px 0!important;background:transparent!important;border:0!important}" +
      ".beta-sharing{margin:3px auto!important;padding:0 2px!important}" +
      ".beta-sharing .panel{border:0!important;box-shadow:none!important;background:transparent!important;padding:0!important;margin:0!important}" +
      ".beta-sharing .sharing-row{display:flex!important;gap:4px!important;margin:0!important}" +
      ".beta-sharing .sharing-row input{height:40px!important;min-height:40px!important;padding:6px 8px!important;font-size:13px!important}" +
      ".beta-sharing .sharing-row .btn{min-height:40px!important;padding:6px 10px!important;font-size:12px!important;white-space:nowrap}" +
      ".beta-sharing .message,.beta-sharing .song,.beta-sharing .song small,#sharedNow{font-size:12px!important;line-height:1.35!important}" +
      "#sharedNow:empty,#sharedNow[hidden]{display:none!important}" +
      "footer{font-size:12px!important;line-height:1.3!important;padding:6px 2px!important;margin-top:2px!important;text-transform:none!important;display:flex!important;gap:6px;flex-wrap:wrap;border-top:1px solid #46535d!important}" +
      "footer a{font-size:12px!important}";
    document.head.appendChild(style);
  }

  function detailsFromPanel(panel, title) {
    if (!panel || panel.tagName === "DETAILS") return panel;
    var heading = panel.querySelector("h2");
    var details = document.createElement("details");
    var summary = document.createElement("summary");
    var body = document.createElement("div");
    details.className = "panel compact-utility";
    summary.textContent = title;
    body.className = "compact-utility-body";
    Array.prototype.slice.call(panel.childNodes).forEach(function (node) {
      if (node !== heading) body.appendChild(node);
    });
    details.appendChild(summary);
    details.appendChild(body);
    panel.parentNode.replaceChild(details, panel);
    return details;
  }

  function collapseRobotHelp() {
    Array.prototype.some.call(document.querySelectorAll(".panel p.message"), function (paragraph) {
      if (paragraph.textContent.trim().indexOf("1 = every tick; 2 = half speed;") !== 0) return false;
      var details = document.createElement("details");
      var summary = document.createElement("summary");
      var copy = document.createElement("div");
      details.className = "compact-help";
      summary.textContent = "Boring stuff";
      copy.className = "compact-copy";
      copy.textContent = paragraph.textContent.trim();
      details.appendChild(summary);
      details.appendChild(copy);
      paragraph.parentNode.replaceChild(details, paragraph);
      return true;
    });
  }

  function collapsePatternFiles() {
    Array.prototype.some.call(document.querySelectorAll(".panel"), function (panel) {
      var heading = panel.querySelector("h2");
      if (!heading || heading.textContent.trim().toLowerCase() !== "pattern files") return false;
      detailsFromPanel(panel, "Pattern files");
      return true;
    });
  }

  function compactExistingDisclosures() {
    Array.prototype.forEach.call(document.querySelectorAll("details.panel"), function (details) {
      var summary = details.querySelector("summary");
      if (!summary) return;
      var label = summary.textContent.trim().toLowerCase();
      if (details.classList.contains("beta-recordings")) {
        details.classList.add("compact-utility");
        var first = summary.querySelector("span");
        if (first) first.textContent = "Recordings";
        details.removeAttribute("open");
      } else if (label.indexOf("how to link grids") === 0) {
        details.classList.add("compact-utility");
        details.removeAttribute("open");
      }
    });
    var advanced = document.getElementById("advanced");
    if (advanced) {
      advanced.classList.add("compact-utility");
      advanced.removeAttribute("open");
      var summary = advanced.querySelector("summary");
      if (summary) summary.textContent = "Advanced settings";
    }
  }

  function simplifySharing() {
    var save = document.getElementById("saveCurrentBtn");
    if (save) {
      save.textContent = "Save song";
      save.setAttribute("aria-label", "Save song on this device");
    }
    var shared = document.getElementById("sharedNow");
    if (!shared) return;
    function tidy() {
      var value = shared.textContent.trim();
      var emptyStatus = value === "You are not sharing a song yet." || value === "Saved locally · Sharing offline";
      shared.hidden = emptyStatus || !value;
    }
    tidy();
    if (root.MutationObserver) new MutationObserver(tidy).observe(shared, {childList:true, subtree:true, characterData:true});
  }

  function simplifyFooter() {
    var footer = document.querySelector("footer");
    if (!footer) return;
    var privacy = document.querySelector('a[href="metrics-privacy.html"]');
    var privacyParent = privacy && privacy.parentNode;
    footer.textContent = "Cellbeat Mini · 4 ticks/beat · local songs";
    if (privacy) {
      footer.appendChild(document.createTextNode(" · "));
      footer.appendChild(privacy);
      if (privacyParent && privacyParent !== footer && !privacyParent.textContent.trim()) privacyParent.remove();
    }
  }

  function upgradeUtilities() {
    compactStyle();
    collapseRobotHelp();
    collapsePatternFiles();
    compactExistingDisclosures();
    simplifySharing();
    simplifyFooter();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", upgradeUtilities);
  else upgradeUtilities();
}(this));
