problem_answers = {};

function problem_check_answers() {
    var e = document.getElementById(this.dataset.problemid);
    var problem_node = document.getElementById(problem_id)
    var inputs = problem_node.getElementsByTagName('input');
    var answer_id = "";
    for (index = 0; index < inputs.length; ++index) {
        if (inputs[index].getAttribute('type') == 'checkbox' || inputs[index].getAttribute('type') == 'radio') {
            if (inputs[index].checked) {
                if (answer_id == "") {
                    answer_id = inputs[index].id;
                } else {
                    answer_id = answer_id + "-" + inputs[index].id;
                }
            }
        }
    }
    if (answer_id != "") {
        problem_node.children[0].innerHTML = problem_answers[problem_id][answer_id];
        trigger_seq_content_change_behaviour();
    }
}

$(window).on('load', function () {
    const probemBtns = document.getElementsByClassName("zim-problem_btn");
    for (var i = 0; i < probemBtns.length; ++i) {
        probemBtns[i].addEventListener("click", problem_check_answers);
    }
});