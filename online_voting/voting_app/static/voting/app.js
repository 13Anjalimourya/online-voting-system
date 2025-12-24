function votePopup() {
    if (!confirm("Are you sure you want to submit your vote?")) {
        return false;
    }

    const popup = document.getElementById("popup");
    popup.style.display = "block";

    setTimeout(() => {
        popup.style.display = "none";
    }, 2000);

    return true;
}
