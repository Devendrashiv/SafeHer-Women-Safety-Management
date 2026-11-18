let safeHerMap;
let safeHerMarker;

function showMap(lat, lon) {
  const mapElement = document.getElementById("map");
  if (!mapElement || !window.L) return;
  if (!safeHerMap) {
    safeHerMap = L.map("map").setView([lat, lon], 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(safeHerMap);
  } else {
    safeHerMap.setView([lat, lon], 15);
  }
  if (safeHerMarker) safeHerMarker.remove();
  safeHerMarker = L.marker([lat, lon]).addTo(safeHerMap).bindPopup("Your shared location").openPopup();
}

function requestLocation(onSuccess, onError) {
  if (!navigator.geolocation) {
    onError("Geolocation is not supported by this browser.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    position => onSuccess(position.coords.latitude, position.coords.longitude),
    () => onError("Location permission was denied or location is unavailable."),
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
  );
}

document.addEventListener("DOMContentLoaded", () => {
  const locateButton = document.getElementById("locateButton");
  if (locateButton) locateButton.addEventListener("click", () => {
    locateButton.disabled = true;
    requestLocation((lat, lon) => {
      showMap(lat, lon);
      locateButton.disabled = false;
    }, error => {
      alert(error);
      locateButton.disabled = false;
    });
  });

  const sosButton = document.getElementById("sosButton");
  if (sosButton) sosButton.addEventListener("click", () => {
    const message = document.getElementById("sosMessage");
    if (!confirm("Record an SOS alert in SafeHer? This does not contact emergency services.")) return;
    sosButton.disabled = true;
    message.textContent = "Getting location…";
    const submitAlert = async (latitude, longitude) => {
      try {
        const response = await fetch(window.SAFEHER_SOS_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ latitude, longitude, message: "SOS alert initiated from user dashboard." })
        });
        const result = await response.json();
        message.textContent = result.message || "Alert processed.";
        if (latitude !== null) showMap(latitude, longitude);
      } catch {
        message.textContent = "Could not save the alert. Please try again.";
      } finally {
        sosButton.disabled = false;
      }
    };
    requestLocation((lat, lon) => submitAlert(lat, lon), () => submitAlert(null, null));
  });
});
