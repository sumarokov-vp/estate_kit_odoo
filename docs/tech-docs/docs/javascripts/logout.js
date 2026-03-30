document.addEventListener("DOMContentLoaded", function () {
  var header = document.querySelector(".md-header__inner");
  if (!header) return;
  var btn = document.createElement("a");
  btn.href = "/cdn-cgi/access/logout";
  btn.textContent = "Выйти";
  btn.style.cssText =
    "color:white;margin-left:auto;padding:0.4rem 0.8rem;font-size:0.75rem;opacity:0.8;text-decoration:none;";
  btn.addEventListener("mouseenter", function () { btn.style.opacity = "1"; });
  btn.addEventListener("mouseleave", function () { btn.style.opacity = "0.8"; });
  header.appendChild(btn);
});
