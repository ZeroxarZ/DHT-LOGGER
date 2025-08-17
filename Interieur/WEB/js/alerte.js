const codeDept = "76"; // Ton département
fetch(`/api/secheresse?code=${codeDept}`)
  .then(response => response.json())
  .then(dep => {
    let niveau = dep.niveauGraviteMax;
    let message = "";
    let color = "#b38f00";
    if (niveau === null) {
      message = "Aucune restriction d'eau en vigueur actuellement.";
      color = "#2e7d32";
    } else if (niveau === "vigilance") {
      message = "Vigilance sécheresse en cours. Soyez attentif à votre consommation d'eau.";
      color = "#fbc02d";
    } else if (niveau === "alerte") {
      message = "Alerte sécheresse : restrictions modérées en vigueur.";
      color = "#f57c00";
    } else if (niveau === "alerte_renforcee") {
      message = "Alerte renforcée : restrictions strictes sur l'usage de l'eau.";
      color = "#d84315";
    } else if (niveau === "crise") {
      message = "Crise sécheresse : restrictions maximales, usage de l'eau très limité.";
      color = "#b71c1c";
    }
    document.getElementById("niveau-secheresse").textContent = message;
    document.querySelector(".alert-details").style.color = color;
  })
  .catch(() => {
    document.getElementById("niveau-secheresse").textContent = "Erreur lors de la connexion à l'API Vigieau.";
  });

const apiUrl = "/api/secheresse_all"; // Passe par ton serveur pour éviter les soucis CORS
const carteUrl = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson";

// Palette de couleurs selon le niveau
const couleurs = {
    null: "#e0e0e0", // pas d'alerte
    vigilance: "#fbc02d",
    alerte: "#f57c00",
    alerte_renforcee: "#d84315",
    crise: "#b71c1c"
};

// 1. Récupère les données Vigieau
Promise.all([
    fetch(apiUrl).then(r => r.json()),
    fetch(carteUrl).then(r => r.json())
]).then(([vigieau, geojson]) => {
    // Associe le niveau à chaque département
    const niveaux = {};
    vigieau.forEach(dep => {
        niveaux[dep.code] = dep.niveauGraviteMax;
    });

    // 2. Affiche la carte avec D3.js
    const width = Math.min(500, window.innerWidth - 30), height = 600;
    const svg = d3.select("#carte-secheresse")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const projection = d3.geoConicConformal()
        .center([2.454071, 46.279229])
        .scale(width * 4.2)
        .translate([width / 2, height / 2]);

    const path = d3.geoPath().projection(projection);

    svg.selectAll("path")
        .data(geojson.features)
        .enter()
        .append("path")
        .attr("d", path)
        .attr("fill", d => couleurs[niveaux[d.properties.code]] || "#e0e0e0")
        .attr("stroke", "#888")
        .attr("stroke-width", 0.5)
        .on("mouseover", function(event, d) {
            d3.select(this).attr("stroke-width", 2);
            const niveau = niveaux[d.properties.code] || "Aucune";
            const nom = d.properties.nom;
            showTooltip(event, `<b>${nom} (${d.properties.code})</b><br>Niveau : <b>${niveau.replace("_", " ")}</b>`);
        })
        .on("mouseout", function() {
            d3.select(this).attr("stroke-width", 0.5);
            hideTooltip();
        });

    // Légende améliorée
    const legend = d3.select("#carte-secheresse")
        .append("div")
        .attr("class", "legend-secheresse");
    legend.html(`
        <span style="background:${couleurs.crise};color:white;">Crise</span>
        <span style="background:${couleurs.alerte_renforcee};color:white;">Alerte renforcée</span>
        <span style="background:${couleurs.alerte};color:white;">Alerte</span>
        <span style="background:${couleurs.vigilance};color:black;">Vigilance</span>
        <span style="background:${couleurs.null};color:black;">Aucune</span>
    `);

    // Tooltip
    const tooltip = d3.select("body").append("div")
        .attr("id", "tooltip-carte")
        .style("position", "absolute")
        .style("background", "#fffbe7")
        .style("border", "1px solid #b38f00")
        .style("padding", "8px 12px")
        .style("border-radius", "6px")
        .style("pointer-events", "none")
        .style("font-size", "15px")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.08)")
        .style("display", "none");

    function showTooltip(event, html) {
        tooltip.html(html)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 20) + "px")
            .style("display", "block");
    }
    function hideTooltip() {
        tooltip.style("display", "none");
    }
});

// Recherche d'un département par numéro
document.getElementById("btn-search").onclick = searchDept;
document.getElementById("dept-search").addEventListener("keyup", function(e) {
    if (e.key === "Enter") searchDept();
});

function searchDept() {
    const code = document.getElementById("dept-search").value.trim().padStart(2, "0").toUpperCase();
    if (!code.match(/^\d{2,3}$|^2A$|^2B$/)) {
        document.getElementById("dept-info").textContent = "Numéro de département invalide.";
        return;
    }
    fetch(`/api/secheresse?code=${code}`)
        .then(r => r.json())
        .then(dep => {
            if (dep.error) {
                document.getElementById("dept-info").textContent = "Département non trouvé.";
                return;
            }
            let niveau = dep.niveauGraviteMax;
            let niveauTxt = "Aucune restriction";
            let color = "#2e7d32";
            if (niveau === "vigilance") {
                niveauTxt = "Vigilance sécheresse";
                color = "#fbc02d";
            } else if (niveau === "alerte") {
                niveauTxt = "Alerte sécheresse";
                color = "#f57c00";
            } else if (niveau === "alerte_renforcee") {
                niveauTxt = "Alerte renforcée";
                color = "#d84315";
            } else if (niveau === "crise") {
                niveauTxt = "Crise sécheresse";
                color = "#b71c1c";
            }
            document.getElementById("dept-info").innerHTML = `
                <b>${dep.nom} (${dep.code})</b><br>
                Niveau : <span style="color:${color};font-weight:bold">${niveauTxt}</span><br>
                ${dep.niveauGraviteSupMax ? "Restriction SUP <small>(eaux superficielles)</small> : <b>" + dep.niveauGraviteSupMax + "</b><br>" : ""}
                ${dep.niveauGraviteSouMax ? "Restriction SOU <small>(eaux souterraines)</small> : <b>" + dep.niveauGraviteSouMax + "</b><br>" : ""}
                ${dep.niveauGraviteAepMax ? "Restriction AEP <small>(eau potable)</small> : <b>" + dep.niveauGraviteAepMax + "</b><br>" : ""}
            `;
        })
        .catch(() => {
            document.getElementById("dept-info").textContent = "Erreur lors de la récupération des données.";
        });
}