var aladinOverlay = A.graphicOverlay({ color: "#ee2345", lineWidth: 3 });
var aladinCatalog = A.catalog({ name: "Targets", onClick: "showPopup" });

function add_target_to_sky_map(
  aladin,
  aladinOverlay,
  ra,
  dec,
  target_name,
  color = "blue"
) {
  var coord = new Coo(ra, dec, "deg");

  if (!target_name) {
    target_name = "Unnamed Target";
  }

  // Use built-in marker with specified color
  var source = A.marker(coord, {
    popupTitle: target_name,
    popupDesc: "RA: " + ra.toFixed(6) + ", Dec: " + dec.toFixed(6),
    color: color,
  });
  aladinCatalog.addSources([source]);

  // Add a circle around the target
  aladinOverlay.add(A.circle(ra, dec, 0.04, { color: "red" }));
}
function handle_uploaded_csv(aladin, uploaded_csv_file) {
  // Make an AJAX request to your Flask route with the uploaded CSV file
  var formData = new FormData();
  formData.append("csv_file", uploaded_csv_file);

  $.ajax({
    url: "/csv_upload",
    type: "POST",
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {
      console.log("Data received from server:", data);

      // Create a new catalog object and add it to Aladin Lite
      aladinCatalog = A.catalog({ name: "Targets", onClick: "showPopup" });
      aladin.addCatalog(aladinCatalog);

      var sumRa = 0;
      var sumDec = 0;
      var numTargets = data.length;

      function processTarget(target, ra, dec) {
        console.log("Adding target to sky map:", target);
        add_target_to_sky_map(
          aladin,
          aladinOverlay,
          ra,
          dec,
          target.target_name,
          "red"
        );
        sumRa += parseFloat(ra);
        sumDec += parseFloat(dec);

        // Check if all targets have been processed
        if (aladinCatalog.getSources().length === numTargets) {
          // Calculate the average RA and DEC, and move the sky map to that position
          var avgRa = sumRa / numTargets;
          var avgDec = sumDec / numTargets;
          aladin.gotoRaDec(avgRa, avgDec);
        }
      }

      // Loop through the returned targets
      data.forEach(function (target) {
        if (target.ra && target.dec) {
          // If target has RA and DEC, call processTarget immediately
          processTarget(target, target.ra, target.dec);
        } else if (target.target_name) {
          // If target has a target name, resolve it to RA and DEC using aladin.gotoObject
          aladin.gotoObject(target.target_name, function (found) {
            if (found) {
              var ra = aladin.view.getRa();
              var dec = aladin.view.getDec();
              processTarget(target, ra, dec);
            } else {
              console.error(
                "Error: Target name not found:",
                target.target_name
              );
            }
          });
        } else if (target.tic_id) {
          // If target has a TIC ID, make an AJAX request to the /lookup_tic Flask route
          $.ajax({
            url: "/lookup_tic",
            method: "POST",
            data: { tic_id: "TIC " + target.tic_id },
            success: function (data) {
              var ra = data.ra;
              var dec = data.dec;
              processTarget(target, ra, dec);
            },
            error: function () {
              console.error("Error: TIC ID not found:", target.tic_id);
            },
          });
        }
      });
    },

    error: function (jqXHR, textStatus, errorThrown) {
      console.error("Error uploading CSV file:", textStatus, errorThrown);
    },
  });
}

// Then, initialize the Aladin Lite instance and set up the form submission event

var target = "{{ target }}";
var aladin = A.aladin("#aladin-lite-div", {
  target: target,
  fov: 0.5,
  survey: "P/DSS2/color",
  reticleColor: "#ffeb3b",
  reticleSize: 22,
});
aladin.addCatalog(aladinCatalog);
aladin.addOverlay(aladinOverlay);
$("form").submit(function (event) {
  event.preventDefault();
  target = $("#target").val();
  console.log("Form submitted, target:", target);

  var formData = new FormData();
  formData.append("csv_file", $("#csv-file")[0].files[0]);

  if (target) {
    // Check if the input is in RA/Dec format
    var raDecPattern = /^(\s*-?\d+(\.\d*)?)\s*,\s*(-?\d+(\.\d*)?)\s*$/;
    var raDecMatch = target.match(raDecPattern);

    if (raDecMatch) {
      var ra = parseFloat(raDecMatch[1]);
      var dec = parseFloat(raDecMatch[2]);
      aladin.gotoRaDec(ra, dec);
      add_target_to_sky_map(aladin, aladinOverlay, ra, dec, target, "red");
    }
    // Check if the input is a TIC ID (assuming it starts with 'TIC') or a number
    else if (target.toUpperCase().startsWith("TIC") || !isNaN(target)) {
      if (!target.toUpperCase().startsWith("TIC")) {
        target = "TIC " + target;
      }
      console.log("Submitting TIC ID request:", target);
      $.ajax({
        url: "/lookup_tic",
        method: "POST",
        data: { tic_id: target },
        success: function (data) {
          var ra = data.ra;
          var dec = data.dec;
          aladin.gotoRaDec(ra, dec);
          add_target_to_sky_map(aladin, aladinOverlay, ra, dec, target, "red");
        },
        error: function () {
          alert("Error: TIC ID not found");
        },
      });
    } else {
      // Handle target name input
      console.log("Trying to resolve target name:", target);
      aladin.gotoObject(target);

      // Use setTimeout() to delay the execution of the code after the view has updated
      setTimeout(function () {
        var raDec = aladin.getRaDec();
        var ra = raDec[0];
        var dec = raDec[1];

        // Check if the target is within the view after the delay
        if (Math.abs(aladin.getFov()[0]) >= 0.0001) {
          console.log("Target name found:", target);
          add_target_to_sky_map(aladin, aladinOverlay, ra, dec, target, "red");
        } else {
          console.error("Error: Target name not found:", target);
          alert("Error: Target name not found");
        }
      }, 1000); // Adjust the delay as needed (in milliseconds)
    }
  }

  // Check if a CSV file is uploaded
  if ($("#csv-file")[0].files[0]) {
    // Call handle_uploaded_csv() function to upload CSV file and add markers to the sky map
    handle_uploaded_csv(aladin, $("#csv-file")[0].files[0]);
  }
});
