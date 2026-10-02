// Smart multilingual language switcher with chapter synchronization
(function() {
  function getTargetLanguage() {
    var path = window.location.pathname;
    if (path.includes("/zh/")) return "en";
    if (path.includes("/en/")) return "zh";
    return "en";
  }

  function doSwitch(targetLang) {
    try {
      localStorage.setItem("preferred_lang", targetLang);
    } catch (e) {}

    var currentPath = window.location.pathname;
    var targetPath = "";

    if (targetLang === "en") {
      if (currentPath.includes("/zh/")) {
        targetPath = currentPath.replace("/zh/", "/en/");
      } else {
        targetPath = "../en/index.html";
      }
    } else {
      if (currentPath.includes("/en/")) {
        targetPath = currentPath.replace("/en/", "/zh/");
      } else {
        targetPath = "../zh/index.html";
      }
    }

    var hash = window.location.hash || "";

    fetch(targetPath, { method: "HEAD" })
      .then(function(res) {
        if (res.ok) {
          window.location.href = targetPath + hash;
        } else {
          window.location.href = (targetLang === "en" ? "../en/index.html" : "../zh/index.html");
        }
      })
      .catch(function() {
        window.location.href = targetPath + hash;
      });
  }

  function setupUI() {
    var targetLang = getTargetLanguage();
    var isZh = (targetLang === "en");
    var labelText = isZh ? "🌐 English" : "🌐 中文版";
    var titleText = isZh ? "Switch to English edition of this page" : "切换至本页中文版";

    // Top-right floating pill button
    if (!document.getElementById("floating-lang-toggle")) {
      var floatBtn = document.createElement("button");
      floatBtn.id = "floating-lang-toggle";
      floatBtn.type = "button";
      floatBtn.title = titleText;
      floatBtn.innerHTML = labelText;
      floatBtn.style.cssText = [
        "position: fixed",
        "top: 14px",
        "right: 22px",
        "z-index: 10000",
        "display: inline-flex",
        "align-items: center",
        "gap: 6px",
        "padding: 5px 14px",
        "font-size: 0.85rem",
        "font-weight: 600",
        "color: #1a1a1a",
        "background: rgba(255, 255, 255, 0.95)",
        "backdrop-filter: blur(8px)",
        "-webkit-backdrop-filter: blur(8px)",
        "border: 1px solid #d0d7de",
        "border-radius: 20px",
        "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12)",
        "cursor: pointer",
        "transition: all 0.2s ease"
      ].join("; ");

      floatBtn.onmouseover = function() {
        floatBtn.style.transform = "translateY(-1px)";
        floatBtn.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.18)";
        floatBtn.style.borderColor = "#0969da";
        floatBtn.style.color = "#0969da";
      };
      floatBtn.onmouseout = function() {
        floatBtn.style.transform = "none";
        floatBtn.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.12)";
        floatBtn.style.borderColor = "#d0d7de";
        floatBtn.style.color = "#1a1a1a";
      };

      floatBtn.onclick = function(e) {
        e.preventDefault();
        doSwitch(targetLang);
      };

      document.body.appendChild(floatBtn);
    }

    // AI translation banner on English edition pages
    if (window.location.pathname.includes("/en/")) {
      var mainContent = document.querySelector("main.content");
      if (mainContent && !document.getElementById("ai-translation-banner")) {
        var banner = document.createElement("div");
        banner.id = "ai-translation-banner";
        banner.className = "alert alert-warning alert-dismissible fade show";
        banner.style.cssText = "font-size: 0.86rem; margin-top: 5px; margin-bottom: 20px; border-left: 4px solid #f59f00; background: #fff9db; color: #7c4a03; padding: 10px 16px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);";
        banner.innerHTML = '<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 10px;">' +
          '<div><strong>🤖 AI Translation Draft:</strong> This English edition is currently translated with AI assistance and is not guaranteed to be free of stylistic or contextual flaws. Upon completion of the full Chinese manuscript, the author will personally rewrite the English edition with culturally tailored examples.</div>' +
          '<button type="button" class="btn-close" style="font-size: 0.7rem; padding: 0.2rem;" aria-label="Close" onclick="document.getElementById(\'ai-translation-banner\').remove();"></button>' +
          '</div>';

        var titleHeader = mainContent.querySelector("#title-block-header");
        if (titleHeader) {
          mainContent.insertBefore(banner, titleHeader);
        } else {
          mainContent.insertBefore(banner, mainContent.firstChild);
        }
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupUI);
  } else {
    setupUI();
  }
})();
