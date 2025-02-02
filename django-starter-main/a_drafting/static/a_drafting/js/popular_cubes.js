function showMore(levelSlug) {
    const row = document.getElementById(`row-${levelSlug}`);
    const seeMoreButton = document.querySelector(`button.see-more-button[data-level-slug="${levelSlug}"]`);
    let page = parseInt(seeMoreButton.getAttribute('data-page'), 10) || 2;

    fetch(`/drafting/api/popular-cubes/?level=${levelSlug}&page=${page}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not OK');
            }
            return response.json();
        })
        .then(data => {
            // Append each new cube wrapped in an anchor so it's clickable.
            data.cubes.forEach(cube => {
                const anchor = document.createElement("a");
                anchor.href = `/drafting/cube/${cube.id}/`;
                
                const cubeDiv = document.createElement("div");
                cubeDiv.classList.add("cube-card");
                cubeDiv.innerHTML = `
                    <img src="${cube.image_url}" alt="Cube Image" class="cube-image">
                    <h3>${cube.name}</h3>
                    <p>Created by: ${cube.creator}</p>
                    <p>Drafted ${cube.draft_count} times</p>
                `;
                anchor.appendChild(cubeDiv);
                row.appendChild(anchor);
            });
            // Update the See More button's attributes.
            if (data.has_more) {
                seeMoreButton.setAttribute('data-page', page + 1);
                seeMoreButton.setAttribute('data-has-more', 'true');
            } else {
                seeMoreButton.setAttribute('data-has-more', 'false');
                // Hide the See More button if there are no new cubes to load.
                seeMoreButton.style.display = 'none';
            }
            
            // Create a Collapse button if one doesn't exist.
            let collapseButton = document.querySelector(`button.collapse-button[data-level-slug="${levelSlug}"]`);
            if (!collapseButton) {
                collapseButton = document.createElement("button");
                collapseButton.classList.add("collapse-button");
                collapseButton.setAttribute('data-level-slug', levelSlug);
                collapseButton.textContent = '– Collapse';
                // Insert the Collapse button immediately after the See More button.
                seeMoreButton.parentNode.insertBefore(collapseButton, seeMoreButton.nextSibling);
                
                collapseButton.addEventListener('click', () => {
                    // Remove all extra anchor elements beyond the first 4.
                    const anchors = row.querySelectorAll("a");
                    Array.from(anchors).forEach((anchor, index) => {
                        if (index >= 4) {
                            row.removeChild(anchor);
                        }
                    });
                    // Reset the See More button's page attribute.
                    seeMoreButton.setAttribute('data-page', '2');
                    // Remove the Collapse button.
                    collapseButton.parentNode.removeChild(collapseButton);
                    // Re-display the See More button even if data-has-more was "false".
                    seeMoreButton.style.display = 'inline-block';
                });
            }
        })
        .catch(error => console.error('Error loading more cubes:', error));
}
