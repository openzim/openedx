function show_sidemenu(){
  var e=document.getElementsByClassName("zim-course-index")[0];
  var course_content = document.getElementById("zim-course-content");
  if(e.style.display == 'none' || e.style.display == '') {
    e.style.display = 'block';
    course_content.style.display = 'none';
  }else{
    e.style.display = 'none';
    if (window.matchMedia('(max-width: 640px)').matches) {
      course_content.style.display = 'block';
    }else{
      course_content.style.display = 'table-cell';
    }
  }
}

function show_pagemobilemenu(){
  var e=document.getElementsByClassName("zim-courseware")[0];
  if(e.style.display == 'none' || e.style.display == '') {
    e.style.display = 'block';
  }else{
    e.style.display = 'none';
  }
}

function show_forum_menu(){
  var e=document.getElementsByClassName("forum-nav")[0];
  var forum_content = document.getElementById("main");
  if(e.style.display == 'none' || e.style.display == '') {
    e.style.display = 'block';
    forum_content.style.display = 'none';
  }else{
    e.style.display = 'none';
    if (window.matchMedia('(max-width: 640px)').matches) {
      forum_content.style.display = 'block';
    }else{
      forum_content.style.display = 'table-cell';
    }
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
    if(e.style.display == 'block' || e.style.display == '') {
        e.style.display = 'none';
    }else{
        e.style.display = 'block';
    }
    elem.children[0].children[0].classList.toggle("fa-caret-down");
    elem.children[0].children[0].classList.toggle("fa-caret-right");
}

