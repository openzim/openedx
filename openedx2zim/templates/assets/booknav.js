function booknav_change() {
    if (window.matchMedia('(max-width: 640px)').matches) { // On mobile, we launch download of pdf
        return true;
    } else {
        document.getElementById("viewer-frame").src = this.href;
        return false;
    }
}

$(window).on('load', function () {
    const chapters = document.getElementsByClassName("zim-chapter");
    for (var i = 0; i < chapters.length; ++i) {
        chapters[i].addEventListener("click", booknav_change);
    }
});