document.addEventListener("DOMContentLoaded", function () {
  const links = document.querySelectorAll(".sidebar-menu a");
  links.forEach(link => {
    link.addEventListener("click", function () {
      links.forEach(l => l.classList.remove("active"));
      this.classList.add("active");
    });
  });
});
