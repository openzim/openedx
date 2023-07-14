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


function show_forum(){
  var e = document.getElementById(this.dataset.threadsid);
  if(e.style.display == 'none') {
    e.style.display = 'block';
  }else{
    e.style.display = 'none';
  }
}

function toggle_visibility_submenu(){
    var e = this.nextSibling.nextSibling;
    if(e.style.display == 'block' || e.style.display == '') {
        e.style.display = 'none';
    }else{
        e.style.display = 'block';
    }
    this.children[0].children[0].classList.toggle("fa-caret-down");
    this.children[0].children[0].classList.toggle("fa-caret-right");
}


$(window).on('load', function () {
  const chapters = document.getElementsByClassName("zim-button-chapter");
  for (var i = 0; i < chapters.length; ++i) {
    chapters[i].addEventListener("click", toggle_visibility_submenu);
  }
  
  const mobileMenu = document.getElementById("zim-show_pagemobilemenu")
  if (mobileMenu) {
    mobileMenu.addEventListener("click", show_pagemobilemenu);
  }
  
  const sidemenus = document.getElementsByClassName("zim-side_menu");
  for (var i = 0; i < sidemenus.length; ++i) {
    sidemenus[i].addEventListener("click", show_sidemenu);
  }
  
  const forummenus = document.getElementsByClassName("zim-forum_menu");
  for (var i = 0; i < forummenus.length; ++i) {
    forummenus[i].addEventListener("click", show_forum_menu);
  }
  
  const forumLinks =  document.getElementsByClassName("zim-forum_link");
  for (var i = 0; i < forumLinks.length; ++i) {
    forumLinks[i].addEventListener("click", show_forum);
  }
});
