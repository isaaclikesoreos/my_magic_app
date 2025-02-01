function showMore(levelSlug) {
    const row = document.getElementById(`row-${levelSlug}`);
    const seeMoreButton = document.querySelector(`#row-${levelSlug} + .see-more-button`);

    // Select all cards in the row
    const allCubes = Array.from(row.querySelectorAll(".cube-card"));

    // Check if there are hidden cubes
    const isExpanded = allCubes.some(cube => !cube.classList.contains("hidden"));

    if (isExpanded) {
        // Collapse to show only the first 4 cubes
        allCubes.forEach((cube, index) => {
            if (index >= 4) cube.classList.add("hidden");
        });
        seeMoreButton.textContent = "See More";
    } else {
        // Expand to show all cubes
        allCubes.forEach(cube => cube.classList.remove("hidden"));
        seeMoreButton.textContent = "Show Less";
    }
}
