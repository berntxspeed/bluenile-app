
$(function(){

    // main script
    $(document).ready(function () {
        // render drill down view A for a specific email
        $("#a-side .send-select, #a-side .email-select").on('change', function () {
            var sendId = $(this).val();
            var emlSendGrapher = new EmlSendGrapher();
            emlSendGrapher.init('#drill-down-areaA', sendId);
        });

        // render drill down view B for a specific email
        $("#b-side .send-select, #b-side .email-select").on('change', function () {
            var sendId = $(this).val();
            var emlSendGrapher = new EmlSendGrapher();
            emlSendGrapher.init('#drill-down-areaB', sendId);
        });
    });
});

