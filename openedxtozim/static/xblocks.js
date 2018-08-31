var problem_answers_array={};
var problem_explanation_array={};
var problem_hint_array={};
function problem_check_answers(problem_id){
  inputs_valid = Array.prototype.slice.call(document.getElementById(problem_id).getElementsByClassName("show_answers_valid"));
  inputs_invalid = Array.prototype.slice.call(document.getElementById(problem_id).getElementsByClassName("show_answers_invalid"));
  inputs_noans = Array.prototype.slice.call(document.getElementById(problem_id).getElementsByClassName("no_answers"));
  inputs = inputs_valid.concat(inputs_invalid, inputs_noans);
  for (index = 0; index < inputs.length; ++index) {
	inputs[index].parentNode.style.border = "2px solid #e3e3e3";
        inputs[index].remove();
  }
  var not_available = document.createElement("span");
  not_available.classList.add("fa");
  not_available.classList.add("fa-question");
  not_available.classList.add("no_answers");
  not_available.title="This answers can't be check";

  var valid = document.createElement("span");
  valid.classList.add("fa");
  valid.classList.add("fa-check");
  valid.classList.add("show_answers_valid");
  valid.title="This answers is valid";

  var invalid = document.createElement("span");
  invalid.classList.add("fa");
  invalid.classList.add("fa-times");
  invalid.classList.add("show_answers_invalid");
  invalid.title="This answers invalid";

  var inputs_input = document.getElementById(problem_id).getElementsByTagName('input');
  for (index = 0; index < inputs_input.length; ++index) {
    if(inputs_input[index].getAttribute('type') == 'checkbox' || inputs_input[index].getAttribute('type') == 'radio'){
      if(inputs_input[index].checked){
        console.log(index);
        if (problem_answers_array[problem_id].indexOf(inputs_input[index].id) > -1){
          inputs_input[index].parentNode.appendChild(valid.cloneNode(true));
          inputs_input[index].parentNode.style.border = "2px solid green";
        }else{
          inputs_input[index].parentNode.appendChild(invalid.cloneNode(true));
          inputs_input[index].parentNode.style.border = "2px solid red";
        }
      }
    }else{
      inputs_input[index].parentNode.appendChild(not_available.cloneNode(true));
    }
  }
}

function problem_show_answers(problem_id){
  inputs_valid = Array.prototype.slice.call(document.getElementById(problem_id).getElementsByClassName("show_answers_valid"));
  inputs_invalid = Array.prototype.slice.call(document.getElementById(problem_id).getElementsByClassName("show_answers_invalid"));
  inputs = inputs_valid.concat(inputs_invalid);
  for (index = 0; index < inputs.length; ++index) {
	inputs[index].parentNode.style.border = "2px solid #e3e3e3";
        inputs[index].remove();
  }

  var valid = document.createElement("span");
  valid.classList.add("fa");
  valid.classList.add("fa-check");
  valid.classList.add("show_answers_valid");
  valid.title="This answers is valid";

  problem_answers_array[problem_id].forEach(function(item,index,array){

      try{
        document.getElementById(item).parentNode.appendChild(valid.cloneNode(true));
        document.getElementById(item).parentNode.style.border = "2px solid green";
      } catch(e) {}
    }
  );
  problem_explanation_array[problem_id].forEach(function(item,index,array){
      document.getElementById(ans).parentNode.style.display= "block";
      document.getElementById(ans).innerHTML= problem_explanation_array[problem_id][ans];
  });
}

function problem_hint(problem_id){
  let hint = problem_hint_array[problem_id];
  let text= "<strong>Hint (" + hint["hint_index"]+1 + " of " + hint["total_possible"] + ") : " + hint["msg"];
  document.getElementById("hint-"+problem_id).style.display= "block";
  document.getElementById("hint-content-"+problem_id).innerHTML = text;

  let next= document.getElementById("hint-next-"+problem_id);
  next.disabled= hint["should_enable_next_hint"];
}


