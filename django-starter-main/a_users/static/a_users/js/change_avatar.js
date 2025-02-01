function toggleAvatarSelection() {
    const selectionDiv = document.getElementById('avatar-selection');
    if (selectionDiv.classList.contains('hidden-avatar')) {
        selectionDiv.classList.remove('hidden-avatar');
        selectionDiv.classList.add('visible-avatar');
        console.log("Avatar selection made visible");
    } else {
        selectionDiv.classList.remove('visible-avatar');
        selectionDiv.classList.add('hidden-avatar');
        console.log("Avatar selection hidden");
    }
}
