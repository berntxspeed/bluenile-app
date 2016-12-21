
var updateBar = function(percent){
    jQuery('.bar').css({'width': percent + '%'});
    jQuery('.bar').html(percent + '%')
}

// poll state of the current task
var PollState = function(task_id) {
$.ajax({
              url: '/task_update' ,
              data: {"task_id": task_id},
              dataType: "json",
              contentType: "application/json",
    }).done(function(task){
     console.log(task);
     var finished = false;
     if (task.result && task.result.process_percent) {
      updateBar(task.result.process_percent)
     }
     if (task.state) {
      jQuery('.status').html(task.state);
      if (task.state == 'FAILURE'){
        jQuery('.status').html(task.state + "<br/>" + task.result)
        finished = true;
      }
      else if (task.state =='SUCCESS'){
        //be sure to complete the task bar
        updateBar(100);
        finished = true;
      }
     };

     // create the infinite loop of Ajax calls to check the state
     // of the current task
     if (finished == false)
        setTimeout(function() {
            PollState(task_id);
        }, 2000)
    });
}