
function trigger_seq_content_change_behaviour() {
    $('#seq_content').append("<div id='dummy_div'></div>");
    $('#dummy_div').remove();
}

$(window).on('load', function () {
    trigger_seq_content_change_behaviour();
});