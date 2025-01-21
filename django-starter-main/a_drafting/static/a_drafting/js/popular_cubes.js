function showMore(levelSlug) {
    // Get the cube row and the button
    const row = document.getElementById(`row-${levelSlug}`);
    const seeMoreButton = document.querySelector(`#row-${levelSlug} + .see-more-button`);

    // Find all hidden cubes in the row
    const hiddenCubes = row.querySelectorAll(".cube-card.hidden");

    if (hiddenCubes.length > 0) {
        // Show hidden cubes
        hiddenCubes.forEach(cube => cube.classList.remove("hidden"));
        seeMoreButton.textContent = "Show Less";
    } else {
        // Hide cubes beyond the first 4
        const allCubes = row.querySelectorAll(".cube-card");
        allCubes.forEach((cube, index) => {
            if (index >= 4) cube.classList.add("hidden");
        });
        seeMoreButton.textContent = "See More";
    }
}
