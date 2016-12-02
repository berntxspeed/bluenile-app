

// poll state of the current task
var PollState = function(task_id) {
$.ajax({
              url: 'http://localhost:5000/task_update' ,
              data: {"task_id": task_id},
              dataType: "json",
              contentType: "application/json",
    }).done(function(task){
     console.log(task);
     var finished = false;
     if (task.process_percent) {
      jQuery('.bar').css({'width': task.process_percent + '%'});
      jQuery('.bar').html(task.process_percent + '%')
     } else {
      jQuery('.status').html(task);
      if (task=='SUCCESS' || task == 'FAILURE')
        finished = true;
     };

     // create the infinite loop of Ajax calls to check the state
     // of the current task
     if (finished == false)
        PollState(task_id);
    });
}