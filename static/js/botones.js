document.addEventListener("DOMContentLoaded", () => {
  const back = document.getElementById("btnBack");
  const home = document.getElementById("btnHome");
  if (back) back.addEventListener("click", () => history.back());
  if (home) home.addEventListener("click", () => window.location.href = "/");
});
    