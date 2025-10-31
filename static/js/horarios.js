document.addEventListener("DOMContentLoaded", () => {
  const fechaInput = document.querySelector("input[name='fecha']");
  const horaSelect = document.querySelector("select[name='hora']");
  const servicio = "{{ servicio }}";

  fechaInput.addEventListener("change", async () => {
    const fecha = fechaInput.value;
    if (!fecha) return;

    horaSelect.innerHTML = "<option>Cargando...</option>";

    try {
      const res = await fetch(`/api/horas-libres?fecha=${fecha}&servicio=${encodeURIComponent(servicio)}`);
      const data = await res.json();

      horaSelect.innerHTML = "";

      if (data.ok && data.horas.length > 0) {
        data.horas.forEach(h => {
          const opt = document.createElement("option");
          opt.value = h;
          opt.textContent = h;
          horaSelect.appendChild(opt);
        });
      } else {
        horaSelect.innerHTML = "<option>No hay horas libres</option>";
      }
    } catch (err) {
      console.error("Error al obtener horas:", err);
      horaSelect.innerHTML = "<option>Error al cargar horas</option>";
    }
  });
});
