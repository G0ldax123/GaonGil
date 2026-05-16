(() => {
  const routes = {
    "0": { folder: "0_AnimaPackage-Html-JrLyP", source: "0" },
    "1": { folder: "1-2_AnimaPackage-Html-bgKUq", source: "1" },
    "1-1": { folder: "1-2_AnimaPackage-Html-bgKUq", source: "1-1" },
    "1-2": { folder: "1-2_AnimaPackage-Html-bgKUq", source: "1-2" },
    "1-3": { folder: "1-3_AnimaPackage-Html-GVlcp", source: "1-3" },
    "1-4": { folder: "1-4_AnimaPackage-Html-aQOi4", source: "1-4" },
    "2": { folder: "2_AnimaPackage-Html-pNcR1", source: "2" },
    "2-1-1": { folder: "2-1-1_AnimaPackage-Html-ucQkB", source: "2-1-1" },
    "2-1-2": { folder: "2-1-2_AnimaPackage-Html-iqd8r", source: "2-1-2" },
    "2-2-1": { folder: "2-2-1_AnimaPackage-Html-7yJUt", source: "2-2-1" },
    "2-2-2": { folder: "2-2-2_AnimaPackage-Html-MYsDP", source: "2-2-2" },
    "3": { folder: "3_AnimaPackage-Html-IamA3", source: "3" },
    "4": { folder: "4_AnimaPackage-Html-FRsGb", source: "4" },
    "4-1": { folder: "4-1_AnimaPackage-Html-PTB8M", source: "4-1" },
    "4-2": { folder: "4-2_AnimaPackage-Html-ytt8O", source: "4-2" },
    "4-3": { folder: "4-3_AnimaPackage-Html-NrmjJ", source: "4-3" },
    "5": { folder: "5_AnimaPackage-Html-6Yoja", source: "5" },
  };

  if (typeof window === "undefined") {
    startServer();
    return;
  }

  const screen = getScreen();
  if (!screen) return;

  applyFrame();
  applyUserTypePatch(screen);
  applyEnterTransition();

  if (screen === "0") {
    window.setTimeout(() => goTo("1", { type: "dissolve", duration: 310 }), 900);
  }

  if (screen === "3") {
    window.setTimeout(() => goTo("4", { type: "slide-left", duration: 600 }), 2500);
  }

  let lastMoveAt = 0;
  document.addEventListener("pointerup", handleActivate, true);
  document.addEventListener("click", handleActivate, true);

  function handleActivate(event) {
    const now = Date.now();
    if (now - lastMoveAt < 250) return;

    const next = getNextScreen(event);
    if (!next) return;

    lastMoveAt = now;
    event.preventDefault();
    event.stopPropagation();
    goTo(next.screen, next.transition);
  }

  function getScreen() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    const alias = (parts[0] || "").replace(/\.html$/i, "");
    return routes[alias] ? routes[alias].source : null;
  }

  function getNextScreen(event) {
    const point = getPoint(event);

    if (screen === "0") {
      return { screen: "1", transition: { type: "dissolve", duration: 310 } };
    }

    if (screen === "1") {
      if (isInside(point, [20, 260, 180, 425])) {
        return { screen: "1-1", transition: { type: "dissolve", duration: 310 } };
      }
      if (isInside(point, [180, 260, 345, 425])) {
        return { screen: "1-2", transition: { type: "dissolve", duration: 310 } };
      }
      if (isInside(point, [20, 425, 180, 600])) {
        return { screen: "1-3", transition: { type: "dissolve", duration: 310 } };
      }
      if (isInside(point, [180, 425, 345, 600])) {
        return { screen: "1-4", transition: { type: "dissolve", duration: 310 } };
      }
      return null;
    }

    if (["1-1", "1-2", "1-3", "1-4"].includes(screen)) {
      if (isInside(point, [240, 70, 360, 130])) {
        return { screen: "1", transition: { type: "dissolve", duration: 310 } };
      }
      if (isInside(point, [18, 630, 345, 735])) {
        return { screen: "2", transition: { type: "slide-left", duration: 450 } };
      }
    }

    if (["2", "2-1-1", "2-1-2", "2-2-1", "2-2-2"].includes(screen)) {
      if (isInside(point, [240, 70, 360, 130])) {
        return { screen: "1", transition: { type: "slide-right", duration: 450 } };
      }
    }

    if (screen === "2") {
      if (isInside(point, [24, 300, 338, 360])) {
        return { screen: "2-1-1", transition: { type: "dissolve", duration: 600 } };
      }
    }

    if (screen === "2-1-1") {
      if (isInside(point, [40, 420, 320, 455])) {
        return { screen: "2-1-2", transition: { type: "dissolve", duration: 600 } };
      }
    }

    if (screen === "2-1-2") {
      if (isInside(point, [20, 418, 182, 475])) {
        return { screen: "2", transition: { type: "slide-right", duration: 700 } };
      }
      if (isInside(point, [24, 360, 338, 410])) {
        return { screen: "2-2-1", transition: { type: "dissolve", duration: 600 } };
      }
    }

    if (screen === "2-2-1") {
      if (isInside(point, [40, 470, 320, 515])) {
        return { screen: "2-2-2", transition: { type: "dissolve", duration: 600 } };
      }
    }

    if (screen === "2-2-2") {
      if (isInside(point, [20, 418, 182, 475])) {
        return { screen: "2", transition: { type: "slide-right", duration: 700 } };
      }
      if (isInside(point, [180, 418, 342, 475])) {
        return { screen: "3", transition: { type: "dissolve", duration: 600 } };
      }
    }

    if (screen === "4") {
      if (isInside(point, [240, 70, 360, 130])) {
        return { screen: "1", transition: { type: "slide-right", duration: 450 } };
      }
      if (isInside(point, [230, 300, 342, 405])) {
        return { screen: "4-1", transition: { type: "slide-left", duration: 450 } };
      }
      if (isInside(point, [230, 418, 342, 530])) {
        return { screen: "4-2", transition: { type: "slide-left", duration: 450 } };
      }
      if (isInside(point, [230, 540, 342, 660])) {
        return { screen: "4-3", transition: { type: "slide-left", duration: 450 } };
      }
      if (isInside(point, [80, 665, 280, 730])) {
        return { screen: "5", transition: { type: "slide-left", duration: 450 } };
      }
    }

    if (["4-1", "4-2", "4-3"].includes(screen)) {
      if (isInside(point, [235, 70, 360, 130])) {
        return { screen: "4", transition: { type: "slide-right", duration: 450 } };
      }
    }

    if (screen === "5") {
      if (isInside(point, [240, 70, 360, 130])) {
        return { screen: "1", transition: { type: "slide-right", duration: 450 } };
      }
      if (isInside(point, [95, 610, 270, 690])) {
        return { screen: "4", transition: { type: "slide-right", duration: 450 } };
      }
    }

    return null;
  }

  function goTo(alias, transition) {
    if (!routes[alias]) return;

    const config = transition || { type: "dissolve", duration: 310 };
    sessionStorage.setItem("gaonGilTransition", JSON.stringify(config));
    applyExitTransition(config);

    window.setTimeout(() => {
      window.location.href = new URL(`/${alias}/index.html`, window.location.href).href;
    }, Math.min(config.duration, 180));
  }

  function applyFrame() {
    const style = document.createElement("style");
    style.textContent = `
      html,
      body {
        width: 100% !important;
        min-width: 0 !important;
        min-height: 100% !important;
        margin: 0 !important;
        background: #ffffff !important;
      }

      body {
        display: flex !important;
        justify-content: center !important;
        align-items: flex-start !important;
        min-height: 100vh !important;
        padding-top: max(0px, calc((100vh - 780px) / 2)) !important;
        padding-bottom: max(0px, calc((100vh - 780px) / 2)) !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
      }

      .element,
      .screen,
      .label {
        width: 360px !important;
        min-width: 360px !important;
        max-width: 360px !important;
        min-height: 780px !important;
        flex: 0 0 360px !important;
      }
    `;
    document.head.appendChild(style);
  }

  function applyUserTypePatch(currentScreen) {
    if (!["1", "1-1"].includes(currentScreen)) return;

    const crutchCardBackground = document.querySelector(".element .group .rectangle");
    if (crutchCardBackground) {
      crutchCardBackground.setAttribute("src", "img/rectangle-16.png");
    }

    if (currentScreen === "1-1") {
      const wheelchairCardBackground = document.querySelector(".element .div .img");
      const wheelchairIcon = document.querySelector(".element .div .o-2");

      if (wheelchairCardBackground) {
        wheelchairCardBackground.setAttribute("src", "img/rectangle-13.png");
      }

      if (wheelchairIcon) {
        wheelchairIcon.setAttribute("src", "/user_icon_AnimaPackage-Html-zamoW/img/o-2.png");
      }

      const wheelchairCard = document.querySelector(".element .div");
      if (wheelchairCard) {
        wheelchairCard.classList.add("gg-wheelchair-selected");
      }
    }

    const style = document.createElement("style");

    if (currentScreen === "1") {
      style.textContent = `
        .element .group .rectangle { content: url("img/rectangle-16.png") !important; }
        .element .group .o,
        .element .group .image {
          opacity: 0.32 !important;
        }
        .element .rectangle-2 {
          background-color: #e9e9e9 !important;
        }
        .element .text-wrapper-2 {
          color: #000000 !important;
        }
        .element .text-wrapper-6 {
          display: none !important;
        }
      `;
    }

    if (currentScreen === "1-1") {
      style.textContent = `
        .element .group .rectangle { content: url("img/rectangle-16.png") !important; }
        .element .group .o,
        .element .group .image {
          opacity: 0.32 !important;
        }
        .element .div.gg-wheelchair-selected .img {
          opacity: 1 !important;
        }
        .element .div.gg-wheelchair-selected .o-2 {
          top: 2px !important;
          left: 4px !important;
          width: 134px !important;
          height: 134px !important;
          opacity: 1 !important;
          filter: none !important;
        }
        .element .div.gg-wheelchair-selected .image-2 {
          opacity: 0 !important;
        }
        .element .div.gg-wheelchair-selected::after {
          content: "휠체어 이용자";
          position: absolute;
          top: 127px;
          left: 0;
          width: 152px;
          font-family: "Pretendard-Bold", Helvetica, sans-serif;
          font-weight: 700;
          color: #3665fc;
          font-size: 11px;
          text-align: center;
          line-height: 11px;
          letter-spacing: 0;
        }
      `;
    }

    document.head.appendChild(style);
  }

  function applyEnterTransition() {
    const raw = sessionStorage.getItem("gaonGilTransition");
    if (!raw) return;

    sessionStorage.removeItem("gaonGilTransition");

    let transition;
    try {
      transition = JSON.parse(raw);
    } catch {
      return;
    }

    const name =
      transition.type === "slide-left"
        ? "gg-slide-left-in"
        : transition.type === "slide-right"
          ? "gg-slide-right-in"
          : "gg-fade-in";
    const duration = Number(transition.duration || 310);
    animateBody(name, duration);
  }

  function applyExitTransition(transition) {
    const name =
      transition.type === "slide-left"
        ? "gg-slide-left-out"
        : transition.type === "slide-right"
          ? "gg-slide-right-out"
          : "gg-fade-out";
    animateBody(name, Number(transition.duration || 310));
  }

  function animateBody(name, duration) {
    const style = document.createElement("style");
    style.textContent = `
      @keyframes gg-fade-in {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes gg-fade-out {
        from { opacity: 1; }
        to { opacity: 0; }
      }
      @keyframes gg-slide-left-in {
        from { opacity: 0; transform: translateX(36px); }
        to { opacity: 1; transform: translateX(0); }
      }
      @keyframes gg-slide-left-out {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(-36px); }
      }
      @keyframes gg-slide-right-in {
        from { opacity: 0; transform: translateX(-36px); }
        to { opacity: 1; transform: translateX(0); }
      }
      @keyframes gg-slide-right-out {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(36px); }
      }
      body {
        animation: ${name} ${duration}ms ease both !important;
      }
    `;
    document.head.appendChild(style);
  }

  function getPoint(event) {
    const root =
      document.querySelector(".element") ||
      document.querySelector(".screen") ||
      document.querySelector(".label") ||
      document.body;
    const rect = root.getBoundingClientRect();

    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  function isInside(point, area) {
    const [left, top, right, bottom] = area;
    return point.x >= left && point.x <= right && point.y >= top && point.y <= bottom;
  }

  function startServer() {
    const fs = require("fs");
    const http = require("http");
    const path = require("path");

    const port = Number(process.env.PORT || 5173);
    const exportRoot = path.resolve(__dirname, "figma-export");
    const scriptPath = __filename;

    const server = http.createServer((request, response) => {
      const requestUrl = new URL(request.url, `http://${request.headers.host}`);

      if (requestUrl.pathname === "/") {
        redirect(response, "/0/index.html");
        return;
      }

      if (requestUrl.pathname === "/app.js") {
        serveFile(response, scriptPath, "application/javascript; charset=utf-8");
        return;
      }

      const aliasTarget = resolveAliasPath(requestUrl.pathname);
      const target = aliasTarget || safeResolve(exportRoot, decodeURIComponent(requestUrl.pathname));
      if (!target) {
        notFound(response);
        return;
      }

      fs.stat(target, (statError, stats) => {
        if (statError) {
          notFound(response);
          return;
        }

        const filePath = stats.isDirectory() ? path.join(target, "index.html") : target;
        if (!filePath.startsWith(exportRoot)) {
          notFound(response);
          return;
        }

        const type = contentType(filePath);
        if (type.startsWith("text/html")) {
          serveHtml(response, filePath);
          return;
        }

        serveFile(response, filePath, type);
      });
    });

    server.listen(port, "127.0.0.1", () => {
      console.log(`GaonGil prototype: http://127.0.0.1:${port}/`);
      console.log(`Serving original export files from: ${exportRoot}`);
    });

    function resolveAliasPath(urlPath) {
      const parts = decodeURIComponent(urlPath).split("/").filter(Boolean);
      if (parts.length === 0) return null;

      const route = routes[parts[0]];
      if (!route) return null;

      const rest = parts.slice(1);
      const relativePath = rest.length === 0 ? "index.html" : rest.join("/");
      return safeResolve(path.join(exportRoot, route.folder), relativePath);
    }

    function safeResolve(root, requestPath) {
      const resolved = path.resolve(root, `.${requestPath.startsWith("/") ? requestPath : `/${requestPath}`}`);
      return resolved.startsWith(root) ? resolved : null;
    }

    function serveHtml(response, filePath) {
      fs.readFile(filePath, "utf8", (error, html) => {
        if (error) {
          notFound(response);
          return;
        }

        const scriptTag = '<script src="/app.js"></script>';
        const output = html.replace(/<\/body>/i, `${scriptTag}\n</body>`);

        response.writeHead(200, {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
        });
        response.end(output);
      });
    }

    function serveFile(response, filePath, type) {
      fs.readFile(filePath, (error, content) => {
        if (error) {
          notFound(response);
          return;
        }

        response.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store" });
        response.end(content);
      });
    }

    function redirect(response, location) {
      response.writeHead(302, { Location: location });
      response.end();
    }

    function notFound(response) {
      response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Not found");
    }

    function contentType(filePath) {
      const extension = path.extname(filePath).toLowerCase();
      return (
        {
          ".css": "text/css; charset=utf-8",
          ".html": "text/html; charset=utf-8",
          ".js": "application/javascript; charset=utf-8",
          ".json": "application/json; charset=utf-8",
          ".png": "image/png",
          ".jpg": "image/jpeg",
          ".jpeg": "image/jpeg",
          ".svg": "image/svg+xml",
          ".webp": "image/webp",
        }[extension] || "application/octet-stream"
      );
    }
  }
})();
