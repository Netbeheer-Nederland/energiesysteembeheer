document.addEventListener("DOMContentLoaded", async function() {
    const container = document.getElementById('concept-usages');
    const metaTag = document.querySelector('meta[name="concept-uri"]');
    
    // Stop als we niet op een begrippenpagina zijn
    if (!container || !metaTag) return;

    const currentUri = metaTag.getAttribute('content');
    // TODO: allow multiple and move to config
    const jsonPath = 'https://netbeheer-nederland.github.io/stelsel/registers/concept_usages.json'; 

    try {
        const response = await fetch(jsonPath);
        if (!response.ok) throw new Error("JSON niet gevonden");
        
        const data = await response.json();
        
        // --- URI Normalisatie ---
        // Soms heeft de JSON een trailing slash en de meta-tag niet (of andersom)
        // We zoeken naar een exacte match OF een match met/zonder slash
        let usages = data[currentUri];
        
        if (!usages) {
            // Probeer alternatieven (met of zonder slash)
            const altUri = currentUri.endsWith('/') 
                ? currentUri.slice(0, -1) 
                : currentUri + '/';
            usages = data[altUri];
        }

        // Als er geen data is voor dit begrip, doen we niets (container blijft leeg)
        if (!usages || usages.length === 0) return;

        // --- Render HTML ---
        // We gebruiken de styling classes van Just the Docs
        let html = `
            <h2 class="text-delta">Gebruik</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align:left">Model</th>
                            <th style="text-align:left">Element</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        usages.forEach(item => {
            html += `
                <tr>
                    <td style="text-align:left">
                        ${item.model_url ? '<a href="' + item.model_url + '">' + item.model_name + '</a>' : item.model_name}
                    </td>
                    <td style="text-align:left">
                        ${item.element_url ? '<a href="' + item.element_url + '">' + item.element_name + '</a>' : item.element_name}
                        (${item.element_type})
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        // Injecteer de HTML
        container.innerHTML = html;

    } catch (error) {
        console.warn("Kon model usages niet laden:", error);
    }
});
