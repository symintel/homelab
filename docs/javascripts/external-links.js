/*
 * Enlaces externos: abre en una pestaña nueva todo enlace que apunta fuera de este sitio (GitHub, documentación
 * oficial, los servicios *.homelab.local, el botón de editar, etc.), para que quien sigue una guía paso a paso no
 * pierda la página en la que iba. Los enlaces internos y los anclas (#...) no se tocan.
 *
 * Cada enlace queda con rel="noopener" (la pestaña nueva no controla a esta) y con un aviso solo para lectores de
 * pantalla ("se abre en una pestaña nueva"). Sin dependencias ni llamadas de red.
 */
(function (root) {
  "use strict";

  var NOTICE = " (se abre en una pestaña nueva)";

  // true si el enlace es http(s) y su destino no es el sitio actual.
  function isExternal(link, currentHost) {
    var href = link.getAttribute("href");
    if (!href || href.charAt(0) === "#") return false;
    if (link.protocol !== "http:" && link.protocol !== "https:") return false;
    return link.hostname !== currentHost;
  }

  function mark(link, doc) {
    if (link.getAttribute("data-external") === "1") return;
    link.setAttribute("data-external", "1");
    link.setAttribute("target", "_blank");

    var rel = (link.getAttribute("rel") || "").split(/\s+/).filter(Boolean);
    if (rel.indexOf("noopener") === -1) rel.push("noopener");
    link.setAttribute("rel", rel.join(" "));

    // Aviso para lectores de pantalla; oculto a la vista.
    var notice = doc.createElement("span");
    notice.textContent = NOTICE;
    notice.setAttribute(
      "style",
      "position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0"
    );
    link.appendChild(notice);
  }

  function run(doc, host) {
    var links = doc.querySelectorAll("a[href]");
    for (var i = 0; i < links.length; i++) {
      if (isExternal(links[i], host)) mark(links[i], doc);
    }
  }

  function init() {
    run(document, root.location.hostname);
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { isExternal: isExternal, mark: mark, run: run, NOTICE: NOTICE };
  } else if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
    // Si más adelante se activa la navegación instantánea de Material, la página cambia sin recargar.
    if (root.document$ && typeof root.document$.subscribe === "function") root.document$.subscribe(init);
  }
})(typeof window !== "undefined" ? window : this);
