document.addEventListener("DOMContentLoaded", function() {
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark-mode");
    }
});
document.getElementById("themeToggle").addEventListener("click", function() {
    document.body.classList.toggle("dark-mode");
    localStorage.setItem("theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
});
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
}
let dataCache = [];
const maxPoints = 60; // Nombre maximum de points à afficher dans les graphiques

// Récupération des contextes de dessin
const temperatureCtx = document.getElementById('temperatureChart').getContext('2d');
const humidityCtx = document.getElementById('humidityChart').getContext('2d');

// Dégradé pour le graphique de température
const tempGradient = temperatureCtx.createLinearGradient(0, 0, 0, 400);
tempGradient.addColorStop(0, 'rgba(255, 99, 132, 0.5)');
tempGradient.addColorStop(1, 'rgba(255, 99, 132, 0)');

// Dégradé pour le graphique d’humidité
const humidityGradient = humidityCtx.createLinearGradient(0, 0, 0, 400);
humidityGradient.addColorStop(0, 'rgba(54, 162, 235, 0.5)');
humidityGradient.addColorStop(1, 'rgba(54, 162, 235, 0)');

// Options communes
const commonOptions = {
  responsive: true,
  animation: {
    duration: 1500,
    easing: 'easeOutQuart'
  },
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: function(context) {
          const value = context.parsed.y;
          return `${context.dataset.label}: ${value.toFixed(2)} ${context.dataset.label.includes('Temp') ? '°C' : '%'}`;
        }
      }
    }
    // Titre supprimé ici selon ta demande
  }
};

// Graphique de température
const temperatureChart = new Chart(temperatureCtx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Température (°C)',
      data: [],
      borderColor: (ctx) => {
        const values = ctx.chart.data.datasets[0].data;
        return values[ctx.dataIndex] < 0 ? 'rgba(0, 0, 255, 1)' : 'rgba(255, 99, 132, 1)';
      },
      backgroundColor: tempGradient,
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6
    }]
  },
  options: {
    ...commonOptions,
    scales: {
      x: {
        ticks: {
          maxRotation: 45,
          autoSkip: true,
          maxTicksLimit: 10
        },
        title: {
          display: false,
          text: 'Temps'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Température (°C)'
        }
      }
    }
  }
});

// Graphique d’humidité
const humidityChart = new Chart(humidityCtx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Humidité (%)',
      data: [],
      borderColor: 'rgba(54, 162, 235, 1)',
      backgroundColor: humidityGradient,
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6
    }]
  },
  options: {
    ...commonOptions,
    scales: {
      x: {
        ticks: {
          maxRotation: 45,
          autoSkip: true,
          maxTicksLimit: 10
        },
        title: {
          display: false,
          text: 'Temps'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Humidité (%)'
        }
      }
    }
  }
});
// Fonction pour mettre à jour les graphiques et les logs
async function updateCharts() {
    try {
        const response = await fetch("/data");
        const data = await response.json();
        dataCache = data; // Mise à jour du cache des données pour le CSV
        // Mise à jour des graphiques avec toutes les données
        const labels = dataCache.slice(-maxPoints).map(d => d.time);
        const temperatureData = dataCache.slice(-maxPoints).map(d => d.temperature);
        const humidityData = dataCache.slice(-maxPoints).map(d => d.humidity);
        // Mise à jour des graphiques
        temperatureChart.data.labels = labels;
        temperatureChart.data.datasets[0].data = temperatureData;
        temperatureChart.update();
        humidityChart.data.labels = labels;
        humidityChart.data.datasets[0].data = humidityData;
        humidityChart.update();
        // Mise à jour des informations actuelles
        if (data.length > 0) {
            const latest = data[data.length - 1];
            document.getElementById('currentTemperature').textContent = `Température : ${latest.temperature} °C`;
            document.getElementById('currentHumidity').textContent = `Humidité : ${latest.humidity} %`;
            document.getElementById('currentTime').textContent = `Heure : ${latest.time}`;
            // Appelle ta nouvelle fonction d'alerte async ici
            await checkAlert();
        }
        // Logs
        const logList = document.getElementById('logList');
        logList.innerHTML = '';
        data.forEach(entry => {
            const logEntry = document.createElement('div');
            logEntry.textContent = `Identifiant : ${entry.device_id} - ${entry.time} - Température : ${entry.temperature} °C, Humidité : ${entry.humidity} %`;
            logList.appendChild(logEntry);
        });
        // Défilement automatique vers le bas
        logList.scrollTop = logList.scrollHeight;
    } catch (error) {
        // Ne rien faire en cas d'erreur
    }
}

function downloadCSV() {
    const rows = [
        ["Identifiant", "Date/Heure", "Temperature (C)", "Humidite (%)"]
    ];
    dataCache.forEach(entry => {
        rows.push([entry.device_id, entry.time, entry.temperature, entry.humidity]);
    });
    // Utilisation du point-virgule comme séparateur pour Excel FR
    const csvContent = rows.map(e => e.join(";")).join("\n");
    const blob = new Blob([csvContent], {
        type: 'text/csv;charset=utf-8;'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "data.csv";
    a.click();
    URL.revokeObjectURL(url);
    showToast("Fichier CSV téléchargé !");
}

function downloadExcel() {
    const wsData = [
        ["Identifiant", "Date/Heure", "Temperature (C)", "Humidite (%)"]
    ];
    dataCache.forEach(entry => {
        wsData.push([entry.device_id, entry.time, entry.temperature, entry.humidity]);
    });
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    XLSX.utils.book_append_sheet(wb, ws, "Données");
    // Ajouter un graphique au fichier Excel (via `!charts`)
    const chart = {
        "!charts": [{
            type: "line",
            series: [{
                name: "Température (C)",
                values: `Données!B2:B${wsData.length}`
            }, {
                name: "Humidité (%)",
                values: `Données!C2:C${wsData.length}`
            }],
            categories: `Données!A2:A${wsData.length}`,
            title: "Évolution Température & Humidité",
            position: {
                tl: {
                    row: 1,
                    col: 4
                },
                br: {
                    row: 16,
                    col: 10
                }
            }
        }]
    };
    Object.assign(ws, chart); // Injecter le graphique dans la feuille
    // Télécharger le fichier Excel
    XLSX.writeFile(wb, "data.xlsx");
    showToast("Fichier XLSX téléchargé !");
}
// Ajouter un bouton pour télécharger l'Excel
document.getElementById('downloadExcelButton').addEventListener('click', downloadExcel);
// Ajout d'un événement au bouton de téléchargement CSV 
document.getElementById('downloadButton').addEventListener('click', downloadCSV);
// Mise à jour automatique toutes les 10 secondes
setInterval(updateCharts, 10000);
updateCharts(); // Mise à jour initiale
function getCardinalDirection(degrees) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(degrees / 45) % 8;
    return directions[index];
}

function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}min`;
}
async function fetchExternalWeather() {
    const city = 'VILLE,FR'; // Remplacez par la ville souhaitée
    const url = `/api/weather?city=${encodeURIComponent(city)}`;
    const uvUrl = `/api/uv?city=${encodeURIComponent(city)}`;
    showSpinner();
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Erreur API");
        const weather = await response.json();

        // Partie UV
        const uvResponse = await fetch(uvUrl);
        if (!uvResponse.ok) throw new Error("Erreur API UV");
        const uvData = await uvResponse.json();
        document.getElementById('externalUV').textContent = uvData.value;

        const temp = weather.main.temp.toFixed(1);
        const feelsLike = weather.main.feels_like.toFixed(1);
        const humidity = weather.main.humidity;
        const pressure = weather.main.pressure;
        const windSpeed = (weather.wind.speed * 3.6).toFixed(1);
        const windDeg = weather.wind.deg;
        const cloudiness = weather.clouds.all;
        const visibility = weather.visibility / 1000;
        const tempMin = weather.main.temp_min.toFixed(1);
        const tempMax = weather.main.temp_max.toFixed(1);
        const sunrise = weather.sys.sunrise;
        const sunset = weather.sys.sunset;
        const condition = weather.weather[0].main.toLowerCase();
        const now = Math.floor(Date.now() / 1000);
        const isNight = now < sunrise || now > sunset;
        const dayDuration = sunset - sunrise;
        document.getElementById('externalTemp').textContent = temp;
        document.getElementById('externalFeelsLike').textContent = feelsLike;
        document.getElementById('externalHumidity').textContent = humidity;
        document.getElementById('externalPressure').textContent = pressure;
        document.getElementById('externalWind').textContent = windSpeed;
        document.getElementById('externalWindDir').textContent = getCardinalDirection(windDeg);
        document.getElementById('externalClouds').textContent = cloudiness;
        document.getElementById('externalVisibility').textContent = visibility.toFixed(1);
        document.getElementById('externalTempMin').textContent = tempMin;
        document.getElementById('externalTempMax').textContent = tempMax;
        document.getElementById('sunriseTime').textContent = formatTime(sunrise);
        document.getElementById('sunsetTime').textContent = formatTime(sunset);
        document.getElementById('dayDuration').textContent = formatDuration(dayDuration);
        updateWeatherIcon(condition, isNight);
        showToast("Météo mise à jour !");
    } catch (error) {
        showToast("Erreur météo ou UV", 4000);
    } finally {
        hideSpinner();
    }
}

function updateWeatherIcon(condition, isNight) {
    const icon = document.getElementById('weatherIcon');
    icon.className = 'fa-solid fa-2x'; // reset base classes
    // Ajoute une icône de lune si la nuit
    if (isNight) {
        icon.classList.add('fa-moon');
        return;
    }
    switch (condition) {
        case 'clear':
            icon.classList.add('fa-sun');
            break;
        case 'clouds':
            icon.classList.add('fa-cloud');
            break;
        case 'rain':
            icon.classList.add('fa-cloud-showers-heavy');
            break;
        case 'drizzle':
            icon.classList.add('fa-cloud-rain');
            break;
        case 'thunderstorm':
            icon.classList.add('fa-bolt');
            break;
        case 'snow':
            icon.classList.add('fa-snowflake');
            break;
        case 'mist':
        case 'fog':
        case 'haze':
            icon.classList.add('fa-smog');
            break;
        default:
            icon.classList.add('fa-question');
            break;
    }
}
fetch("/user/status").then(res => res.json()).then(user => {
    const authLinks = document.getElementById("authLinks");
    authLinks.innerHTML = "";
    if (user.logged_in) {
        const dropdown = document.createElement("div");
        dropdown.className = "user-dropdown";
        dropdown.innerHTML = `
        <button>
          <i class="fa-solid fa-user"></i> ${user.username} <i class="bi bi-caret-down-fill"></i>
        </button>
        <div class="user-dropdown-content">
          <a href="/profil"><i class="fa-solid fa-user"></i> Profil</a>
          ${user.can_access_panel ? '<a href="/panel"><i class="fa-solid fa-table-columns"></i> Panel</a>' : ''}
          ${user.is_admin ? '<a href="/admin"><i class="fa-solid fa-shield-halved"></i> Admin</a>' : ''}
          <a href="/logout"><i class="fa-solid fa-right-from-bracket"></i> Se déconnecter</a>
        </div>
      `;
        authLinks.appendChild(dropdown);
    } else {
        authLinks.innerHTML = `
      <a href="/login" class="btn auth-btn login-btn">Connexion</a>
      <a href="/register" class="btn auth-btn register-btn">Inscription</a>
    `;
    }
});
async function checkAlert() {
    try {
        const response = await fetch('/api/check_alert');
        const data = await response.json();
        if (data.alert) {
            let alertBubble = document.getElementById('alert-bubble');
            if (!alertBubble) {
                alertBubble = document.createElement('div');
                alertBubble.id = 'alert-bubble';
                alertBubble.style.position = 'fixed';
                alertBubble.style.bottom = '10px';
                alertBubble.style.right = '10px';
                alertBubble.style.backgroundColor = '#f44336';
                alertBubble.style.color = 'white';
                alertBubble.style.padding = '10px';
                alertBubble.style.borderRadius = '5px';
                alertBubble.style.zIndex = '1000';
                document.body.appendChild(alertBubble);
            }
            alertBubble.textContent =
                `Alerte seuil : Temp=${data.temperature}°C (min ${data.temp_min}°C / max ${data.temp_max}°C), ` +
                `Hum=${data.humidity}% (min ${data.humidity_min}% / max ${data.humidity_max}%)`;
            alertBubble.style.display = 'block';
        } else {
            let alertBubble = document.getElementById('alert-bubble');
            if (alertBubble) {
                alertBubble.style.display = 'none';
            }
        }
    } catch (err) {
        console.error("Erreur fetch alert:", err);
    }
}
// Lancer au chargement + toutes les 10 min
fetchExternalWeather();
setInterval(fetchExternalWeather, 600000);
// Affiche un toast de feedback
function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    toast.style.opacity = '1';
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => { toast.style.display = 'none'; }, 300);
    }, duration);
}

function showSpinner() {
    document.getElementById('spinner').style.display = 'flex';
}

function hideSpinner() {
    document.getElementById('spinner').style.display = 'none';
}