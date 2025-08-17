   const searchInput = document.getElementById('searchInput');
   const usersTable = document.getElementById('usersTable').getElementsByTagName('tbody')[0];
   searchInput.addEventListener('input', function() {
       const filter = this.value.toLowerCase();
       Array.from(usersTable.rows).forEach(row => {
           const username = row.cells[1].textContent.toLowerCase();
           row.style.display = username.includes(filter) ? '' : 'none';
       });
   });
   document.addEventListener("DOMContentLoaded", () => {
       const toggle = document.getElementById("darkModeToggle");

       // Load dark mode state from localStorage
       if (localStorage.getItem("darkMode") === "enabled") {
           document.body.classList.add("dark");
       }

       toggle.addEventListener("click", () => {
           document.body.classList.toggle("dark");
           const darkModeEnabled = document.body.classList.contains("dark");
           localStorage.setItem("darkMode", darkModeEnabled ? "enabled" : "disabled");
       });

       // Search input filter
       const searchInput = document.getElementById("searchInput");
       searchInput.addEventListener("keyup", () => {
           const searchTerm = searchInput.value.toLowerCase();
           const rows = document.querySelectorAll("tbody tr");
           rows.forEach((row) => {
               const username = row.querySelector("td").textContent.toLowerCase();
               row.style.display = username.includes(searchTerm) ? "" : "none";
           });
       });
   });