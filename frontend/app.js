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
  const routeRequestKey = "gaonGilRouteRequest";
  const routeResponseKey = "gaonGilRouteResponse";
  const routeErrorKey = "gaonGilRouteError";
  const routeDictionaryKey = "gaonGilRouteDictionary";
  const mainRiskFactorsKey = "gaonGilMainRiskFactors";

  if (typeof window === "undefined") {
    startServer();
    return;
  }

  const screen = getScreen();
  if (!screen) return;

  applyFrame();
  applyUserTypePatch(screen);
  applyResultData(screen);
  applyEnterTransition();

  if (screen === "0") {
    window.setTimeout(() => goTo("1", { type: "dissolve", duration: 310 }), 900);
  }

  if (screen === "3") {
    waitForRecommendation();
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

    if (next.prepareRouteRequest) {
      const saved = saveRouteRequest();
      if (!saved) return;
    }

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
        return { screen: "3", transition: { type: "dissolve", duration: 600 }, prepareRouteRequest: true };
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

  function saveRouteRequest() {
    const startLabel = getText(".element .text-wrapper-5");
    const endLabel = getText(".element .text-wrapper-6");

    if (!startLabel || !endLabel) {
      showRequestError("출발지 또는 도착지 입력값을 읽지 못했습니다.");
      return false;
    }

    const payload = {
      start: startLabel,
      end: endLabel,
      userType: "wheelchair",
    };

    sessionStorage.setItem(routeRequestKey, JSON.stringify(payload));
    sessionStorage.removeItem(routeResponseKey);
    sessionStorage.removeItem(routeErrorKey);
    return true;
  }

  async function waitForRecommendation() {
    const payload = getStoredRouteRequest();
    if (!payload) {
      showRequestError("요청 데이터가 없습니다. 출발지와 도착지를 다시 선택해주세요.");
      return;
    }

    try {
      const data = await requestRecommendation(payload);

      saveRouteDictionaries(data);
      sessionStorage.setItem(routeResponseKey, JSON.stringify(data));
      sessionStorage.removeItem(routeErrorKey);
      goTo("4", { type: "slide-left", duration: 600 });
    } catch (error) {
      const message = normalizeRecommendationError(error);
      sessionStorage.setItem(
        routeErrorKey,
        JSON.stringify({
          message,
          request: payload,
        })
      );
      showRequestError(`경로 요청 실패: ${message}`);
      console.error("GaonGil recommendation request failed", error);
    }
  }

  async function requestRecommendation(payload) {
    const result = await postRecommendation(payload);
    if (!result.response.ok) {
      throwRecommendationError(result.response, result.data);
    }

    return validateRecommendationResult(result.data);
  }

  async function postRecommendation(payload) {
    const response = await fetch(getRecommendEndpoint(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const data = await readJson(response);
    return { response, data };
  }

  function throwRecommendationError(response, data) {
    const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }

  function normalizeRecommendationError(error) {
    if (error instanceof TypeError) {
      return "백엔드 응답을 받지 못했습니다. 서버 실행 상태와 API 주소를 확인해주세요.";
    }

    if (error instanceof Error && error.message) {
      return error.message;
    }

    return "백엔드 응답을 받지 못했습니다.";
  }

  function validateRecommendationResult(data) {
    if (!data || typeof data !== "object") {
      throw new Error("백엔드 응답을 받지 못했습니다.");
    }

    if (!Array.isArray(data.routes)) {
      throw new Error("백엔드 응답 형식이 올바르지 않습니다. routes 배열이 없습니다.");
    }

    return data;
  }

  function getStoredRouteRequest() {
    const raw = sessionStorage.getItem(routeRequestKey);
    if (!raw) return null;

    try {
      const payload = JSON.parse(raw);
      if (!payload || !payload.start || !payload.end) return null;
      return {
        start: String(payload.start),
        end: String(payload.end),
        userType: "wheelchair",
      };
    } catch {
      return null;
    }
  }

  function saveRouteDictionaries(data) {
    const routeDictionary = buildRouteDictionary(data);
    const mainRiskFactorsDictionary = {};

    Object.keys(routeDictionary).forEach((routeId) => {
      const factors = routeDictionary[routeId].mainRiskFactors;
      mainRiskFactorsDictionary[routeId] = Array.isArray(factors) ? factors : [];
    });

    sessionStorage.setItem(routeDictionaryKey, JSON.stringify(routeDictionary));
    sessionStorage.setItem(mainRiskFactorsKey, JSON.stringify(mainRiskFactorsDictionary));
  }

  function applyResultData(currentScreen) {
    if (!["4", "4-1", "4-2", "4-3"].includes(currentScreen)) return;

    const response = getStoredJson(routeResponseKey);
    if (!response) return;

    saveRouteDictionaries(response);

    const orderedRoutes = getOrderedRoutes(response);
    const resultRows = [
      {
        routeIndex: 0,
        recommendationSelector: ".element .text-wrapper-4",
        durationSelector: ".element .div-2 .span",
        summarySelector: ".element .text-wrapper-9",
      },
      {
        routeIndex: 1,
        recommendationSelector: ".element .text-wrapper-5",
        durationSelector: ".element .div-3 .span",
        summarySelector: ".element .text-wrapper-10",
      },
      {
        routeIndex: 2,
        recommendationSelector: ".element .text-wrapper-6",
        durationSelector: ".element .div-4 .span",
        summarySelector: ".element .text-wrapper-11",
      },
    ];

    if (currentScreen === "4") {
      resultRows.forEach(applyRouteText);
      return;
    }

    const detailRows = {
      "4-1": {
        routeIndex: 0,
        recommendationSelector: ".element .text-wrapper-4",
        durationSelector: ".element .div-2 .span",
        summarySelector: ".element > .p",
      },
      "4-2": {
        routeIndex: 1,
        recommendationSelector: ".element .group-4 .text-wrapper-4",
        durationSelector: ".element .group-4 .p .span",
        summarySelector: ".element .group-4 .text-wrapper-6",
      },
      "4-3": {
        routeIndex: 2,
        recommendationSelector: ".element .group-2 .text-wrapper-4",
        durationSelector: ".element .group-2 .p .span",
        summarySelector: ".element .group-2 .text-wrapper-6",
      },
    };

    applyRouteText(detailRows[currentScreen]);

    function applyRouteText(row) {
      if (!row) return;
      const route = orderedRoutes[row.routeIndex];
      if (!route) return;

      replaceTextIfPresent(row.recommendationSelector, route.recommendation || "");
      applyRecommendationColor(row.recommendationSelector, route.recommendation);
      replaceTextIfPresent(row.durationSelector, getRouteDuration(route));
      replaceText(row.summarySelector, route.summary || route.summaryTitle || "");
    }
  }

  function getOrderedRoutes(data) {
    const recommendationOrder = { 안전: 0, 주의: 1, 위험: 2 };
    const responseRoutes = data && Array.isArray(data.routes) ? data.routes : [];

    return responseRoutes
      .filter((route) => route && typeof route === "object")
      .map((route, index) => ({ route, index }))
      .sort((left, right) => {
        const leftOrder = recommendationOrder[left.route.recommendation] ?? 99;
        const rightOrder = recommendationOrder[right.route.recommendation] ?? 99;
        return leftOrder - rightOrder || left.index - right.index;
      })
      .map((entry) => entry.route);
  }

  function buildRouteDictionary(data) {
    const dictionary = {};
    const responseRoutes = data && Array.isArray(data.routes) ? data.routes : [];

    responseRoutes.forEach((route) => {
      if (route && route.routeId) {
        dictionary[route.routeId] = route;
      }
    });

    return dictionary;
  }

  function getStoredJson(key) {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;

    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function normalizeDuration(duration) {
    if (duration === null || duration === undefined || duration === "") return "";
    const numericDuration = Number(duration);
    return Number.isFinite(numericDuration) ? String(numericDuration) : String(duration);
  }

  function getRouteDuration(route) {
    const candidates = [
      route.estimatedMinutes,
      route.duration,
      route.durationMinutes,
      route.estimatedTimeText,
    ];

    for (const candidate of candidates) {
      const duration = normalizeDuration(candidate);
      if (!duration) continue;

      const match = duration.match(/\d+/);
      return match ? match[0] : duration;
    }

    return "";
  }

  function applyRecommendationColor(selector, recommendation) {
    const element = document.querySelector(selector);
    if (!element) return;

    const colors = {
      안전: "#3e7c2e",
      주의: "#edca52",
      위험: "#d4312a",
    };
    const color = colors[recommendation];
    if (color) {
      element.style.color = color;
    }
  }

  function replaceTextIfPresent(selector, text) {
    if (text === null || text === undefined || text === "") return;
    replaceText(selector, text);
  }

  function replaceText(selector, text) {
    const element = document.querySelector(selector);
    if (element) {
      element.textContent = text;
    }
  }

  function getRecommendEndpoint() {
    const configuredBase =
      window.GAONGIL_API_BASE_URL ||
      sessionStorage.getItem("gaonGilApiBaseUrl") ||
      `http://${window.location.hostname || "127.0.0.1"}:8000`;
    return `${configuredBase.replace(/\/$/, "")}/recommend`;
  }

  async function readJson(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  function showRequestError(message) {
    const style = document.createElement("style");
    style.textContent = `
      .gg-request-error {
        position: fixed;
        left: 50%;
        top: calc(50% + 105px);
        z-index: 9999;
        width: min(280px, calc(100vw - 48px));
        transform: translateX(-50%);
        color: #ffffff;
        background: rgba(35, 45, 65, 0.92);
        border-radius: 8px;
        padding: 12px 14px;
        box-sizing: border-box;
        font-family: "Pretendard-Regular", Helvetica, sans-serif;
        font-size: 12px;
        line-height: 1.45;
        text-align: center;
      }
    `;
    document.head.appendChild(style);

    const existing = document.querySelector(".gg-request-error");
    if (existing) existing.remove();

    const errorBox = document.createElement("div");
    errorBox.className = "gg-request-error";
    errorBox.textContent = message;
    document.body.appendChild(errorBox);
  }

  function getText(selector) {
    const element = document.querySelector(selector);
    return element ? element.textContent.trim() : "";
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
