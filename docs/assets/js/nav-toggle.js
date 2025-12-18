document.addEventListener("DOMContentLoaded", function() {
    const baseUrl = window.siteConfig?.baseUrl || "";
    const sidebar = document.querySelector('.site-nav');
    const navCategory = document.querySelector('.nav-category');
    const originalList = document.querySelector('.site-nav > .nav-category + .nav-list');
    const azList = document.getElementById('skos-az-list');
    const toggleContainer = document.getElementById('skos-toggle-container');
    const btn = document.getElementById('btn-toggle-nav');
    const loadingContainer = document.getElementById('skos-loading-container');
    const loadingMsg = document.getElementById('skos-loading-msg');

    let dataLoaded = false;
    const jsonUrl = `${baseUrl}/assets/json/alphabetical-nav.json`;

    function scrollToActive() {
        const activeLink = azList.querySelector('.active');
        if (activeLink) activeLink.scrollIntoView({block: 'center'}); 
    }

    function loadAndRenderData() {
        if (dataLoaded) return;

        fetch(jsonUrl)
        .then(response => response.json())
        .then(data => {
            const currentPath = window.location.pathname.replace(/\/$/, "");

            let listHTML = "";

            data.forEach(item => {
            const itemUrlClean = item.url.replace(/\/$/, "");
            const isActive = item.type !== 'alias' && currentPath.endsWith(itemUrlClean);
            let cssClass = 'nav-list-link';
            if (isActive) cssClass += ' active';

            let itemHTML = item.title;
            if (item.type === 'alias') itemHTML = `<span class="text-grey-dk-000">${item.title} &rarr; </span>${item.target_label}`;

            listHTML += '<li class="nav-list-item">';
            listHTML += `<a href="${baseUrl}${item.url}" class="${cssClass}">${itemHTML}</a>`;
            listHTML += '</li>';
            });

            azList.innerHTML = listHTML;
            loadingContainer.style.display = 'none';
            dataLoaded = true;
            scrollToActive();
        })
        .catch(err => {
            loadingMsg.textContent = "Fout bij laden begrippenlijst";
            console.error(err);
        });
    }

    function setNavMode(mode) {
        if (mode === 'az') {
        originalList.style.display = 'none';
        azList.style.display = 'block';
        btn.textContent = 'hiërarchisch';
        localStorage.setItem('skos-nav-pref', 'az');
        if (!dataLoaded) {
            loadAndRenderData(); 
        } else {
            scrollToActive();
        }
        } else {
        originalList.style.display = 'block';
        azList.style.display = 'none';
        btn.textContent = 'alfabetisch'; 
        localStorage.setItem('skos-nav-pref', 'tree');
        }
    }

    if (sidebar && navCategory && originalList && toggleContainer && azList) {
        navCategory.appendChild(toggleContainer);
        toggleContainer.style.display = 'inline';
        sidebar.insertBefore(azList, originalList);
        originalList.id = "skos-tree-list";

        const savedPref = localStorage.getItem('skos-nav-pref');
        if (savedPref === 'az') setNavMode('az');

        btn.addEventListener('click', function() {
        if (azList.style.display === 'none') {
            setNavMode('az');
        } else {
            setNavMode('tree');
        }
        });
    }
});
