/* IMPROUVEMENT rewrite with hidden option */
function show_sidemenu(){
  var e=document.getElementsByClassName("course-index")[0];
  var course_content = document.getElementById("course-content");
  if(e.style.display == 'none' || e.style.display == '') {
    e.style.display = 'block';
    course_content.style.display = 'none';
  }else{
    e.style.display = 'none';
    course_content.style.display = 'table-cell';
  }
}

function show_pagemobilemenu(){
  var e=document.getElementsByClassName("courseware")[0];
  var course_content = document.getElementById("course-content");
  if(e.style.display == 'none' || e.style.display == '') {
    e.style.display = 'block';
    course_content.style.display = 'none';
  }else{
    e.style.display = 'none';
    course_content.style.display = 'table-cell';
  }
}
function show_forum(threads_id){
  var e = document.getElementById(threads_id);
  if(e.style.display == 'none') {
    e.style.display = 'block';
  }else{
    e.style.display = 'none';
  }
}

function toggle_visibility_submenu(elem){
    var e = elem.nextSibling.nextSibling;
    console.log(e);
    if(e.style.display == 'block' || e.style.display == '') {
        e.style.display = 'none';
    }else{
        e.style.display = 'block';
    }
    elem.children[0].children[0].classList.toggle("fa-caret-down");
    elem.children[0].children[0].classList.toggle("fa-caret-right");
}

