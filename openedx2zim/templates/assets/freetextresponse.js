function save_freetext() {
    var text_id = this.dataset.textid
    document.cookie = courseNameSlug + "-" + text_id + "=" + document.getElementById(text_id).value;
}

function load_freetext(text_id) {
    var name = courseNameSlug + "-" + text_id + "=";
    var cookie_split = document.cookie.split(';');
    for (var i = 0; i < cookie_split.length; i++) {
        var c = cookie_split[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(name) == 0) { document.getElementById(text_id).value = c.substring(name.length, c.length); break; }
    }
}

$(window).on('load', function () {
    const courseNameSlug = document.querySelector('meta[name="course_name_slug"]').content

    const studentAnswer = document.getElementsByClassName("student_answer");
    for (var i = 0; i < studentAnswer.length; ++i) {
        load_freetext(studentAnswer[i].id)
    }

    const saveBtns = document.getElementsByClassName("zim-save_freetext");
    for (var i = 0; i < saveBtns.length; ++i) {
        saveBtns[i].addEventListener("click", save_freetext);
    }
});