$(document).ready(function() {
  $("#stockTable").DataTable({ order: [[0, "desc"]] });
  $("#pendingTable").DataTable({ order: [[1, "desc"]] });
  $("#reportTable").DataTable({ order: [[0, "desc"]] });
  $("#completeTable").DataTable({ order: [[1, "desc"]] });
});

// btn-mark-as-fulfilled
$(".btn-mark-as-fulfilled").click(function() {
  var order_id = $(this)
    .parent()
    .siblings(".order_id")
    .html();

  console.log(order_id);
  $.ajax({
    type: "GET",
    url: "../orders/mark_fulfilled/" + order_id + "/"
  }).done(function() {
    // Change order.uploaded to true
    console.log(`succesfully logged order ${order_id}`);
    location.reload();
  });
});

////////////////////////
// ON TOGGLE FUNCTION //
////////////////////////
$(".auto_fulfill-btn").on("change", function() {
  var sku_id = $(this)
    .parent()
    .parent()
    .siblings(".sku_id")
    .html();

  if (this.checked) {
    $.ajax({
      type: "GET",
      url: "../orders/fulfill/" + sku_id + "/on"
    });
  } else {
    $.ajax({
      type: "GET",
      url: "../orders/fulfill/" + sku_id + "/off"
    });
  }
});

////////////////
// Log Button //
////////////////
$(".btn-log ").click(function() {
  var order_id = $(this)
    .parent()
    .siblings(".order_id")
    .html();

  // HARDCODED URL (SWITCHING SHEETS MONTHLY OMEGALUL)
  var sheets_key = "1oUFGr3gqwlvj-tpTjH1NsC9ptKBqD2c8GljXUWA44Zs";

  $.ajax({
    type: "GET",
    url: "../orders/upload/" + order_id + "/" + sheets_key
  }).done(function(msg) {
    if (msg.status == "error") {
      alert("Error Logging Data to Google Sheets");
    }
    // TODO:
    // Change order.uploaded to true
    console.log(`succesfully logged order ${order_id}`);
    location.reload();
  });
});

// Accept Button
$(".btn-accept ").click(function(e) {
  e.preventDefault();
  var order_id = $(this)
    .parent()
    .siblings(".order_id")
    .html();
  $.ajax({
    type: "GET",
    url: "../orders/accept/" + order_id + "/",
    success: function() {
      // On Success
    },
    error: function() {
      // cry for help
    }
  }).done(function(msg) {
    location.reload();
    console.log(msg);
  });
});

// Send order via newegg
$(".btn-send ").click(function() {
  var order_id = $(this)
    .parent()
    .siblings(".order_id")
    .html();
  $.ajax({
    type: "GET",
    url: "../orders/newegg_fulfill/" + order_id + "/"
  }).done(function(msg) {
    location.reload();
    console.log(msg);
  });
});

// Request new tracking report to grab tracking ids
$(".btn-report ").click(function() {
  $.ajax({
    type: "GET",
    url: "../orders/get_report/"
  }).done(function(msg) {
    location.reload();
    console.log(msg);
  });
});

// Parse tracking report to get tracking IDs
$(".btn-parse-report ").click(function() {
  var report_id = $(this)
    .parent()
    .siblings(".report_id")
    .html();
  console.log(report_id);
  $.ajax({
    type: "GET",
    url: "../orders/parse_report/" + report_id + "/",
    error: function() {
      alert(msg.message);
    }
  }).done(function(msg) {
    if (msg.status == "error") {
      alert(msg.message);
    } else {
      location.reload();
    }
  });
});

// Update tracking ID on bestbuy
$(".btn-bestbuy-tracking ").click(function() {
  var order_id = $(this)
    .parent()
    .siblings(".order_id")
    .html();
  var local = $(this).attr('id') === 'local';
  $.ajax({
    type: "GET",
    url: "../orders/update_tracking/" + order_id + "/?local=" + local + "/"
  }).done(function(msg) {
    location.reload();
    console.log(msg);
  });
});

$(".fulfill-button").click(function() {
  $('.fulfill-settings').slideToggle(500);
});