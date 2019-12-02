var interval = 30;		//milliseconds
var refreshInterval=50;	//seconds
var blockPerColumn = 10;

var paddingLeft = 40;
var paddingRight = 150;
var paddingTop = 50;
var paddingBottom = 40;

//don't delete this variable
var resizeTimer;
var intervalCounter = 0;
var isAdapting = false;

//level border color setting
var colorSet = [
	"rgba(255,   0,   0, 0.9)",			//level 0
	"rgba(  0, 255,   0, 0.9)",			//level 1
	"rgba(  0,   0, 255, 0.9)",			//level 2
	"rgba(  0, 255, 255, 0.9)"];		//level 3
var bigBorderWidth = 3;

var portlist = {};
var watchlist = [];
var incident = {};

var selectedPort = 0;

var s;

function first_init() {

	//some fixing on string
	if (!String.prototype.format) {
		String.prototype.format = function () {
			var args = arguments;
			return this.replace(/{(\d+)}/g, function (match, number) {
				return typeof args[number] != 'undefined'
				  ? args[number]
				  : match
				;
			});
		};
	}

	//put current time
	var currentTime = Math.floor((new Date).getTime() / 1000);
	var initTime = currentTime - (currentTime % 300);
	$("#selectedTime").val(initTime - 300);
	$("#selectedTime2").val(initTime );

	s = new DisplayState(document.getElementById('canvas1'));
	console.log("call update from first_init");
	s.option.update();

	//add event listener
	$("input.optionTrigger").bind("click", update_option);
	
	$("#selectedTime").change(function () {
		displayTime("#selectedTime");
		console.log("call update from st1");
		update_option();
	});
	$("#selectedTime2").change(function () {
		displayTime("#selectedTime2");
		console.log("call update from st2");
		update_option();
	});
	$("#seek_left_button").bind("click", function () {
		$("#selectedTime").val(Number($("#selectedTime").val()) - 300).trigger('change');
	});
	$("#seek_right_button").bind("click", function () {
		$("#selectedTime").val(Number($("#selectedTime").val()) + 300).trigger('change');
	});
	$("#seek_left_button2").bind("click", function () {
		$("#selectedTime2").val(Number($("#selectedTime2").val()) - 300).trigger('change');
	});
	$("#seek_right_button2").bind("click", function () {
		$("#selectedTime2").val(Number($("#selectedTime2").val()) + 300).trigger('change');
	});
	$("#preview_add_button").bind("click", function () {
		copyToWatchlist();
	});
	$("#clear_button").bind("click", function () {
		$("#watchList")[0].innerHTML = "";
		watchlist = [];
	});
	
	displayTime("#selectedTime");
	displayTime("#selectedTime2");

	window.onresize = function () {
		if (resizeTimer) {
			clearTimeout(resizeTimer);
		}
		resizeTimer = setTimeout(function () {
			console.log("call from window.onresize");
			update_option();
		}, 500);
	};

	console.log("OK");
}

function checkSearchSubmit(e) {
	if (e.keyCode == 13) {
		$("#searchinput").blur();
		var q = $("#searchinput")[0].value;
		if (q=="") {
			return true;
		}
		else {
			$("#searchbox").mask("loading...");
			$.getJSON('http://203.146.64.37:8080/port/search/', {'q':q}).done(
				function (json) {
					s.searchGroup = json;
					s.option.haveToTriggerValidFlag = true;
					s.option.adaptToChange();
					$("#searchbox").unmask();
					return true;
				}
			)
		}	
	}
}

function getOppositeColor(inColor) {
	var R = (255-parseInt((inColor[1] + inColor[2]), 16)).toString(16);
	var G = (255-parseInt((inColor[3] + inColor[4]), 16)).toString(16);
	var B = (255-parseInt((inColor[5] + inColor[6]), 16)).toString(16);
	if (R.length == 1) R = "0" + R;
	else if (R == "") R = "00";
	if (G.length == 1) G = "0" + G;
	else if (G == "") G = "00";
	if (B.length == 1) B = "0" + B;
	else if (G == "") G = "00";

	return '#' + R + G + B ;
}

function gatherBlink() {
	//calculate new blink list
	newBlink = [];
	for (var incidentID in incident) {
		for (var i = 0; i < incident[incidentID].oids.length; i++) {
			if (newBlink.indexOf(incident[incidentID].oids[i]) == -1) {
				newBlink.push(incident[incidentID].oids[i])
			}
		}
	}
	s.blink = newBlink;
}

function clearRightPanel() {
	var parentNode = $("#incidentList")[0]
	while (parentNode.childNodes.length > 1) {
		console.log(parentNode.childNodes.length);
		console.log(parentNode.childNodes[1]);
		parentNode.removeChild(parentNode.childNodes[1]);
	}
}

function copyToWatchlist() {
	if (s.lookingOID!=-1 && watchlist.indexOf(s.lookingOID) == -1) {
		var bigString = $("#preview_detail")[0].innerHTML;
		bigString=bigString.replace(/preview/g, s.lookingOID);
		bigString = bigString.replace("+", "-");
		bigString = "<div id='{0}_detail' class='port'> {1} </div>".format(s.lookingOID, bigString);
		$(bigString).appendTo("#watchList");
		
		$("." + s.lookingOID + "_image_group").colorbox({ rel: s.lookingOID + '_image_group' });

		$("#" + s.lookingOID + "_add_button").bind("click", function () {
			var removeOID = this.id.split("_")[0];
			var index = watchlist.indexOf(removeOID);
			watchlist.splice(index, 1);
			var parentNode = $("#watchList")[0]
			parentNode.removeChild($("#" + removeOID + "_detail")[0]);
		});

		//put in list
		watchlist.push(s.lookingOID);
	}
	else {
		console.error("Cannot add to watchlist.");
	}
}

function displayTime(target) {
	//console.log("aaa");
	var ttt = new Date(1000 * $(target).val());
	
	if (target == "#selectedTime") {
		$("#datepicker")[0].value = pad2(ttt.getDate())+"/"+pad2(ttt.getMonth()+1)+"/"+ttt.getFullYear();
		//$("#timepicker")[0].value = pad2(ttt.getHours()) + ":" + pad2(ttt.getMinutes());	//this way create a bug
		$("#timepicker").timepicker('setTime', pad2(ttt.getHours()) + ":" + pad2(ttt.getMinutes()));
	}
	else if (target == "#selectedTime2") {
		$("#datepicker2")[0].value = pad2(ttt.getDate()) + "/" + pad2(ttt.getMonth() + 1) + "/" + ttt.getFullYear();
		//$("#timepicker2")[0].value = pad2(ttt.getHours()) + ":" + pad2(ttt.getMinutes());	//this way create a bug
		$("#timepicker2").timepicker('setTime', pad2(ttt.getHours()) + ":" + pad2(ttt.getMinutes()));
	}
}

function update_option() {
	s.option.update();
}

function IsNumeric(num) {
	return (num >= 0 || num < 0);
}

function convertTimestamp(inTimestamp) {
	if (IsNumeric(inTimestamp))
		return new Date(1000 * inTimestamp).toLocaleString();
	else
		return "No timestamp info";
}

function convertRate(inRate) {
	if (IsNumeric(inRate))
		return (inRate / (1024 * 1024)).toFixed(2) + " Mbps";
	else
		return "No traffic info.";

}

function convertPercent(inPercent) {
	if (IsNumeric(inPercent))
		return inPercent.toFixed(2) + ' %';
	else
		return "No % info.";
}

function convertColor(inColor) {
	var lastColor;
	if (inColor == null || inColor.indexOf("#") != 0)
		lastColor = "#333333";
	else
		lastColor = inColor;

	return lastColor; 

}

function DisplayState(canvas) {
	var myState = this;

	this.canvas = canvas;
	this.ctx = canvas.getContext('2d');

	this.group = [];
	this.order = [];

	this.levelBorder = [];
	this.redLink = [];
	this.blink = [];
	this.isBlinkPeriod = false;
	this.searchGroup = [];

	this.hoverIndex = -1;
	this.lookingIndex = -1;
	this.lookingOID = -1;

	this.option = new Option();

	this.valid = true;

	// This complicates things a little but but fixes mouse co-ordinate problems
	// when there's a border or padding. See getMouse for more detail
	var stylePaddingLeft, stylePaddingTop, styleBorderLeft, styleBorderTop;
	if (document.defaultView && document.defaultView.getComputedStyle) {
		this.stylePaddingLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingLeft'], 10) || 0;
		this.stylePaddingTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingTop'], 10) || 0;
		this.styleBorderLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderLeftWidth'], 10) || 0;
		this.styleBorderTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderTopWidth'], 10) || 0;
	}
	// Some pages have fixed-position bars (like the stumbleupon bar) at the top or left of the page
	// They will mess up mouse coordinates and this fixes that
	var html = document.body.parentNode;
	this.htmlTop = html.offsetTop;
	this.htmlLeft = html.offsetLeft;

	// end of setting up

	//about the mouse
	//fixes a problem where double clicking causes text to get selected on the canvas
	canvas.addEventListener('selectstart', function (e) { e.preventDefault(); return false; }, false);
	// Up, down, and move are for dragging

	this.getMouse = function (e) {
		var element = this.canvas, offsetX = 0, offsetY = 0, mx, my;

		// Compute the total offset
		if (element.offsetParent !== undefined) {
			do {
				offsetX += element.offsetLeft;
				offsetY += element.offsetTop;
			} while ((element = element.offsetParent));
		}

		// Add padding and border style widths to offset
		// Also add the <html> offsets in case there's a position:fixed bar
		offsetX += this.stylePaddingLeft + this.styleBorderLeft + this.htmlLeft;
		offsetY += this.stylePaddingTop + this.styleBorderTop + this.htmlTop;

		mx = e.pageX - offsetX;
		my = e.pageY - offsetY;

		// We return a simple javascript object (a hash) with x and y defined
		return { x: mx, y: my };
	}

	this.getTileIndex = function (x, y) {
		var physicalRow = Math.floor((y - paddingTop) / s.option.tileSize);
		var physicalColumn = Math.floor((x - paddingLeft) / s.option.tileSize);
		if (physicalRow < 0 || physicalRow >= s.option.maxRow || physicalColumn < 0)
			return -1;
		var logicalRow = Math.floor(physicalColumn / blockPerColumn) * s.option.maxRow + physicalRow;
		var logicalColumn = physicalColumn % blockPerColumn;
		return logicalRow * blockPerColumn + logicalColumn;
	}

	this.getPhysicalPosition = function (tileIndex) {
		var logicalRow = Math.floor(tileIndex / blockPerColumn);
		var logicalColumn = tileIndex % blockPerColumn;
		var physicalRow = logicalRow % this.option.maxRow;
		var physicalColumn = Math.floor(tileIndex / (blockPerColumn * this.option.maxRow)) * blockPerColumn + logicalColumn;
		return { 'row': physicalRow, 'column': physicalColumn };
	}

	this.getTileIndexFromColumnRow = function(physicalColumn,physicalRow) {
		if (physicalRow < 0 || physicalRow >= s.option.maxRow || physicalColumn < 0)
			return -1;
		var logicalRow = Math.floor(physicalColumn / blockPerColumn) * s.option.maxRow + physicalRow;
		var logicalColumn = physicalColumn % blockPerColumn;
		return logicalRow * blockPerColumn + logicalColumn;
	}

	canvas.addEventListener('mousemove', function (e) {
		var mouse = s.getMouse(e);
		s.hoverIndex = s.getTileIndex(mouse.x, mouse.y);
		s.valid = false;
		$("#status")[0].innerHTML = (s.hoverIndex + " " + mouse.x + " " + mouse.y);

	}, true);

	canvas.addEventListener('click', function (e) {
		var mouse = s.getMouse(e);
		s.lookingIndex = s.getTileIndex(mouse.x, mouse.y);
		if (s.lookingIndex >= 0 && s.lookingIndex < s.order.length) {
			s.lookingOID = s.order[s.lookingIndex];
			s.valid = false;
			$("#status")[0].innerHTML = ("click!!" + " " + mouse.x + " " + mouse.y);

			//get more detail
			if (s.lookingIndex >= 0 && s.lookingIndex < s.order.length) {

				var inputDict = { 'oidList': s.lookingOID };
				if (s.option.timeMode == 1) {
					inputDict['timestampStart'] = s.option.selectedTime;
					inputDict['timestampEnd'] = s.option.selectedTime2;
				}
				console.log(inputDict);
				$.getJSON('http://203.146.64.37:8080/port/getMoreDetail/', inputDict).done(
						function (json) {
							if (json.length == 1) {
								//put data in html
								var portDetail = portlist[s.lookingOID];
								var moreDetail = json[0];
								$("#preview_path")[0].innerHTML = portDetail["source"] + " (" + portDetail["destination"] + ")";
								$("#preview_quick_interface_name")[0].innerHTML =
									  "<a class='preview_image_group' title='Traffic' href='http://cnsmon.csloxinfo.net/{0}/{1}/{2}_bits_Daily.png' >{3}</a>".format(portDetail["eid"], s.lookingOID, s.lookingOID, portDetail["interface"])
									+ "<a hidden class='preview_image_group' title='Packet' href='http://cnsmon.csloxinfo.net/{0}/{1}/{2}_pps_Daily.png' >{3}</a>".format(portDetail["eid"], s.lookingOID, s.lookingOID, portDetail["interface"])
									+ "<a hidden class='preview_image_group' title='Error' href='http://cnsmon.csloxinfo.net/{0}/{1}/{2}_error_Daily.png' >{3}</a>".format(portDetail["eid"], s.lookingOID, s.lookingOID, portDetail["interface"]);

								$(".preview_image_group").colorbox({ rel: 'preview_image_group' });

								$("#preview_traffic_timestamp")[0].innerHTML = "In:" + convertTimestamp(moreDetail["inbound"]["timestamp"]) + "# Out:" + convertTimestamp(moreDetail["outbound"]["timestamp"]);

								//inbound
								$("#preview_inbound_traffic")[0].innerHTML = convertRate(moreDetail["inbound"]["rate"]);
								$("#preview_inbound_percent")[0].innerHTML = convertPercent(moreDetail["inbound"]["percent"]);
								$("#preview_inbound_color")[0].style.backgroundColor = convertColor(moreDetail["inbound"]["color"]);

								//outbound
								$("#preview_outbound_traffic")[0].innerHTML = convertRate(moreDetail["outbound"]["rate"]);
								$("#preview_outbound_percent")[0].innerHTML = convertPercent(moreDetail["outbound"]["percent"]);
								$("#preview_outbound_color")[0].style.backgroundColor = convertColor(moreDetail["outbound"]["color"]);

								//detail at the left side
								$("#preview_node_name")[0].innerHTML = portDetail["source"];
								$("#preview_interface_name")[0].innerHTML = portDetail["interface"]
								$("#preview_target_name")[0].innerHTML = portDetail["destination"];
								if (moreDetail["customer"] == '-') {
									$("#preview_customer")[0].innerHTML = '-';
									$("#preview_location_name")[0].innerHTML = '';
								}
								else {
									$("#preview_customer")[0].innerHTML = moreDetail['customer']['CustName'] + '<a target="_blank" href="http://idcinfo.csloxinfo.net/index.php/project/project_detail/' + moreDetail['customer']['ProjectID'] + '" >' + moreDetail['customer']['ProjectName'] + "</a>";
									$("#preview_location_name")[0].innerHTML = moreDetail['customer']['LocationName'];
								}
								if (moreDetail["ip"] == '-' || moreDetail["ip"]==[] )
									$("#preview_ip")[0].innerHTML = '-';
								else {
									var ans = "VLAN:";
									for (var i = 0; i < moreDetail["vlan"].length; i++)
										ans += moreDetail["vlan"][i] + ", ";
									ans+=" || IP:"
									for (var i = 0; i < moreDetail["ip"].length; i++)
										ans += moreDetail["ip"][i] + ", ";
									$("#preview_ip")[0].innerHTML = ans;
								}
								$("#preview_description")[0].innerHTML = moreDetail['description'];
							}
							else {
								console.error("looking index not found");
							}
						})
					.fail(function (jqxhr, textStatus, error) {
						var err = textStatus + ', ' + error;
						console.log("Request Failed: " + err);
					});
			}
			
			if (s.blink.indexOf(s.lookingOID) != -1) {
				clearRightPanel();
				//show incident
				for (var incidentID in incident) {
					if (incident[incidentID].oids.indexOf(s.lookingOID) != -1) {
						//add to rightPanel
						$("#template_incident_timestamp")[0].innerHTML=convertTimestamp(incident[incidentID].timestamp_start);
						$("#template_incident_subject")[0].innerHTML=incident[incidentID].subject;
						$("#template_incident_detail")[0].innerHTML=incident[incidentID].detail;
						var togetherString = "";
						for (var i = 0; i < incident[incidentID].oids.length; i++) {
							var oid = incident[incidentID].oids[i];
							if (oid in portlist)
								togetherString += portlist[oid].source + " -> " + portlist[oid].interface +"<br/>"
						}
						$("#template_incident_together")[0].innerHTML = togetherString;

						var bigString = $("#template_incident_container")[0].innerHTML;
						bigString = bigString.replace(/template/g, incidentID);
						bigString = "<div id='{0}_incident_container' class='incident_container'> {1} </div>".format(incidentID, bigString);
						$(bigString).appendTo("#incidentList");

						$("#" + incidentID + "_incident_button").bind("click", function () {
							var removeID = this.id.split("_")[0];
							$("#rightPanel").mask("acknowledging...");
							$.getJSON('http://203.146.64.37:8080/incident/acknowledge/', { 'incidentID': removeID, 'method': 'button' })
								.done(function (json) {
									var parentNode = $("#incidentList")[0]
									parentNode.removeChild($("#" + removeID + "_incident_container")[0]);
									delete incident[removeID];
									
									gatherBlink();
								})
								.fail(function (jqxhr, textStatus, error) {
									var err = textStatus + ', ' + error;
									console.log("Request Failed: " + err);
								})
								.always(function () {
									$("#rightPanel").unmask();
								})
							;
							
						});

						//put in list
						watchlist.push(s.lookingOID);
					}
				}
				

				$('#rightPanel').show('slide', { direction: 'right' });
			}
			else {
				$('#rightPanel').hide('slide', { direction: 'right' });
				clearRightPanel();
			}
		}
		else {
			//click nothing
			$('#rightPanel').hide('slide', { direction: 'right' });
			clearRightPanel();
		}
	}, true);

	this.clear = function () {
		this.ctx.clearRect(0, 0, this.option.canvasWidth, this.option.canvasHeight);
	}

	this.drawOneTile = function (i) {
		var physical = this.getPhysicalPosition(i);
		
		if (this.option.showBlink==false || this.blink.indexOf(this.order[i]) == -1) {
			//no blink
			this.ctx.fillStyle = portlist[this.order[i]]['color'];
		}
		else {
			if (this.isBlinkPeriod) {
				this.ctx.fillStyle = getOppositeColor(portlist[this.order[i]]['color']);
			}
			else {
				this.ctx.fillStyle = portlist[this.order[i]]['color'];
			}
		}

		this.ctx.fillRect(paddingLeft + (physical.column * this.option.tileSize), paddingTop + (physical.row * this.option.tileSize), this.option.tileSize, this.option.tileSize);

		if (this.searchGroup.indexOf(this.order[i]) != -1) {
			//this.ctx.save();
			this.ctx.beginPath();
			this.ctx.arc(paddingLeft + ((physical.column + 0.5) * this.option.tileSize), paddingTop + ((physical.row + 0.5) * this.option.tileSize), this.option.tileSize / 2.0, 1.75*Math.PI, 0.75 * Math.PI, false);
			this.ctx.fillStyle = 'green';
			this.ctx.fill();
			//this.ctx.restore();
		}

		if (portlist[this.order[i]]['inFilter'] == 0) {
			this.ctx.save();
			var x1 = paddingLeft + (physical.column * this.option.tileSize);
			var y1 = paddingTop + (physical.row * this.option.tileSize);
			var extender=this.option.tileSize/2;
			this.ctx.strokeStyle = '#2554C7';
			this.ctx.beginPath();
			this.ctx.moveTo(x1, y1);
			this.ctx.lineTo(x1 + extender, y1 + extender);
			this.ctx.lineWidth = 1;
			this.ctx.stroke();
			this.ctx.closePath();
			this.ctx.restore();
		}

	}

	this.draw = function () {
		// if our state is invalid, redraw and validate!
		if (!this.valid && !isAdapting) {

			var ctx = this.ctx;
			this.clear();
			//draw area
			//console.log(this.option.tileSize);
			//tile area
			this.ctx.fillStyle = "#ADD8E6";
			this.ctx.fillRect(0+paddingLeft, 0+paddingTop, this.option.canvasWidth-paddingRight-paddingLeft, this.option.canvasHeight-paddingBottom-paddingTop);
			//tiles
			//this.ctx.fillStyle = "rgb(255,255,255)";
			for (var i = 0; i < this.order.length; i++) {				
				this.drawOneTile(i);

			}

			//draw seperator(in case of showing all levels)
			if (this.option.level == "all" && this.levelBorder.length>0) {
				this.ctx.save();
				this.ctx.lineWidth = bigBorderWidth;
				for (var i = 0; i < 4; i++) {
					this.ctx.strokeStyle = colorSet[i];
					for (var j = 0; j < this.levelBorder[i].length; j++) {
						this.ctx.beginPath();
						this.ctx.moveTo(this.levelBorder[i][j].fromx, this.levelBorder[i][j].fromy);
						this.ctx.lineTo(this.levelBorder[i][j].tox, this.levelBorder[i][j].toy);
						this.ctx.stroke();
						this.ctx.closePath();
					}

				}

				this.ctx.restore();
			}

			//draw from mouse hover
			if (this.hoverIndex >= 0 && this.hoverIndex < this.order.length) {
				var targetGroup;
				var i;
				for (i = 0; i < this.group.length; i++) {
					if (this.hoverIndex < this.group[i]["start"] + this.group[i]["count"]) {
						targetGroup = i;
						break;
					}
				}
				
				var startIndex = this.group[targetGroup]["start"];
				var endIndex = startIndex + this.group[targetGroup]["count"];
				//draw edge
				this.ctx.strokeStyle = "rgba(0, 255, 0, 0.5)";	//transparent green
				this.ctx.lineWidth = 4;
				for (i = startIndex; i < endIndex; i++) {
					var physical = this.getPhysicalPosition(i);
					this.ctx.strokeRect(paddingLeft + (physical.column * this.option.tileSize), paddingTop + (physical.row * this.option.tileSize), this.option.tileSize, this.option.tileSize);
				}
				
				//draw color again
				this.ctx.lineWidth = 0;
				for (i = startIndex; i < endIndex; i++) {
					this.drawOneTile(i);
				}
			}
			
			//draw red link (insert at the middile of hover part)
			if (this.option.showRedLink == true) {
				this.ctx.lineWidth = 2;
				for (var i = 0; i < s.redLink.length; i++) {
					
					var oid = s.redLink[i];
					
					if ((oid in portlist) && (portlist[oid]['matched_oid'] in portlist) && portlist[oid]['index'] != null && portlist[portlist[oid]['matched_oid']]['index'] != null) {
						//console.log("red");
						var beginPhysical = this.getPhysicalPosition(portlist[oid]['index']);
						var endPhysical = this.getPhysicalPosition(portlist[portlist[oid]['matched_oid']]['index']);
						var colorCode = portlist[oid]['color'];
						var extender = this.option.tileSize / 2;
						this.ctx.strokeStyle = colorCode;
						this.ctx.beginPath();
						this.ctx.moveTo(paddingLeft + (beginPhysical.column * this.option.tileSize) + extender, paddingTop + (beginPhysical.row * this.option.tileSize) + extender);
						this.ctx.lineTo(paddingLeft + (endPhysical.column * this.option.tileSize) + extender, paddingTop + (endPhysical.row * this.option.tileSize) + extender);
						this.ctx.stroke();
						this.ctx.closePath();
					}
				}
			}

			//continue in hover
			if (this.hoverIndex >= 0 && this.hoverIndex < this.order.length) {
				//draw window (at hoverIndex)
				this.ctx.lineWidth = 2;
				this.ctx.strokeStyle = "rgba(255, 100, 100, 0.9)";
				this.ctx.fillStyle = portlist[this.order[this.hoverIndex]]['color']
				var physical = this.getPhysicalPosition(this.hoverIndex);
				this.ctx.strokeRect(paddingLeft + (physical.column * this.option.tileSize), paddingTop + (physical.row * this.option.tileSize), this.option.tileSize, this.option.tileSize);

				//draw group name
				if (this.option.showGroupName == false) {
					physical = this.getPhysicalPosition(startIndex);
					ctx.fillStyle = "black";
					ctx.font = "bold 16px Arial";
					//put white shadow
					ctx.save();
					ctx.shadowColor = "white";
					ctx.shadowOffsetX = 0;
					ctx.shadowOffsetY = 0;
					ctx.shadowBlur = 10;
					
					ctx.fillText(this.group[targetGroup]["name"], paddingLeft + (physical.column * this.option.tileSize), paddingTop + (physical.row * this.option.tileSize) -2);
					
					//stop shadow
					ctx.restore();
				}
				

				//draw quick detail
				physical = this.getPhysicalPosition(endIndex-1);
				ctx.fillStyle = "black";
				ctx.font = "bold 16px Arial";
				var quickString = "";
				if (this.option.groupBy == "source") {
					quickString = portlist[this.order[this.hoverIndex]]["interface"];
					if (portlist[this.order[this.hoverIndex]]["destination"] != "")
						quickString += ", to " + portlist[this.order[this.hoverIndex]]["destination"];
				}
				else if (this.option.groupBy == "destination") {
					quickString = "from " + portlist[this.order[this.hoverIndex]]["source"] + " @" + portlist[this.order[this.hoverIndex]]["interface"];
				}
				//put white shadow
				ctx.save();
				ctx.shadowColor = "white";
				ctx.shadowOffsetX = 0;
				ctx.shadowOffsetY = 0;
				ctx.shadowBlur = 10;
				ctx.fillText(quickString, paddingLeft + ((physical.column+1) * this.option.tileSize), paddingTop + ((physical.row+1) * this.option.tileSize) + 16 );
				//stop shadow
				ctx.restore();
				//clear stroke
				this.ctx.lineWidth = 0;
				
			}

			//show group name
			if (this.option.showGroupName==true)
			{
				ctx.fillStyle = "black";
				ctx.font = "14px Arial";
				for (i = 0; i < this.group.length; i++) {
					physical = this.getPhysicalPosition(this.group[i]["start"]);
					ctx.fillText(this.group[i]["name"], paddingLeft + (physical.column * this.option.tileSize), paddingTop + (physical.row * this.option.tileSize) - 2);
				}
			}

			//frame at lookingIndex
			if (this.lookingIndex >= 0 && this.lookingIndex < this.order.length) {
				this.ctx.lineWidth = 2;
				this.ctx.strokeStyle = "rgba(0, 255, 0, 0.9)";
				this.ctx.fillStyle = portlist[this.order[this.lookingIndex]]['color']
				var physical = this.getPhysicalPosition(this.lookingIndex);
				this.ctx.strokeRect(paddingLeft + (physical.column * this.option.tileSize), paddingTop + (physical.row * this.option.tileSize), this.option.tileSize, this.option.tileSize);
			}

			//end draw area
			this.valid = true;
		}

	}

	setInterval(function () {
		if(!isAdapting)
			intervalCounter++;

		var currentTime = (Math.floor((new Date).getTime() / 1000));
		if (s.option.timeMode == 0 && currentTime - s.option.lastUpdate > refreshInterval) {
			console.log("update interval!");
			s.option.lastUpdate=currentTime;
			s.option.haveToUpdateColor = true;
			s.option.haveToUpdateIncident = true;
			s.option.haveToTriggerValidFlag = true;
			s.option.adaptToChange();
		}
		if (intervalCounter % 20 == 0) {	
			//switch blinking every ~0.7 second
			s.isBlinkPeriod ^= true;
			if (s.blink.length > 0) {
				s.option.haveToTriggerValidFlag = true;
				s.option.adaptToChange();
			}
		}
		myState.draw();
		//console.info("draw");
	}, interval);
}

function Option() {

	this.level = "";				// "access", "distribute", "core"
	this.groupBy = "";	//"source" , "destination"
	this.filter = true;
	this.showGroupName = false;
	this.showRedLink = false;
	this.showBlink = true;
	this.timeMode = -1;			// 0=last update, 1=fixed time
	this.selectedTime = -1;		//start epoch time
	this.selectedTime2 = -1;	//end epoch time

	this.canvasWidth = -1;
	this.canvasHeight = -1;

	this.tileSize = -1;
	this.maxRow = -1;

	//to do list (step-by-step)
	this.haveToInitPort = false;
	this.haveToCalculateTileSize = false;
	this.haveToCalculateGroupAndOrder = false;
	this.haveToCalculateLevelBorder = false;
	this.haveToUpdateColor = false;
	this.haveToUpdateIncident = false;
	this.haveToTriggerValidFlag = false;

	//timer
	this.lastUpdate = (Math.floor((new Date).getTime() / 1000));

	this.update = function () {
		console.log("update");
		
		var level_has_been_changed = false;
		var groupBy_has_been_changed = false;
		var filter_has_been_changed = false;
		var showGroupName_has_been_changed = false;
		var showRedLink_has_been_changed = false;
		var showBlink_has_been_change = false;
		var timeMode_has_been_changed = false;
		var canvasSize_has_been_changed = false;

		var newLevel = $('input[name="level"]:checked').val();
		if (this.level != newLevel) {
			level_has_been_changed = true;
			this.level = newLevel;
		}
		var newGroupBy = $('input[name="group"]:checked').val();
		if (this.groupBy != newGroupBy) {
			groupBy_has_been_changed = true;
			this.groupBy = newGroupBy;
		}
		var newFilter = $('input[name="filter"]').prop('checked');
		if (this.filter != newFilter) {
			filter_has_been_changed = true;
			this.filter = newFilter;
		}
		var newShowGroupName = $('input[name="showGroupName"]').prop('checked');
		if (this.showGroupName != newShowGroupName) {
			showGroupName_has_been_changed=true;
			this.showGroupName=newShowGroupName;
		}
		var newShowRedLink = $('input[name="showRedLink"]').prop('checked');
		if (this.showRedLink != newShowRedLink) {
			showRedLink_has_been_changed = true;
			this.showRedLink = newShowRedLink;
		}
		var newShowBlink = $('input[name="showBlink"]').prop('checked');
		if (this.showBlink != newShowBlink) {
			showBlink_has_been_change = true;
			this.showBlink = newShowBlink;
		}

		var newTimeMode = Number( $('input[name="time"]:checked').val());
		var newSelectedTime = $('input[name="selectedTime"]').val();
		var newSelectedTime2 = $('input[name="selectedTime2"]').val();
		if (this.timeMode != newTimeMode || (newTimeMode == 1 && (this.selectedTime != newSelectedTime || this.selectedTime2 != newSelectedTime2))) {
			timeMode_has_been_changed = true;
			this.timeMode = newTimeMode;
			if (newTimeMode == 1) {
				this.selectedTime = newSelectedTime;
				this.selectedTime2 = newSelectedTime2;
			}
		}
		var newWidth = document.documentElement.clientWidth;
		var newHeight = document.documentElement.clientHeight - 150;
		if (this.canvasWidth != newWidth || this.canvasHeight != newHeight) {
			canvasSize_has_been_changed = true;
			this.canvasWidth = newWidth;
			this.canvasHeight = newHeight;

			//reset canvas size (not resize but new size)
			s.canvas = document.getElementById('canvas1');
			s.canvas.setAttribute("width", this.canvasWidth);
			s.canvas.setAttribute("height", this.canvasHeight);
			s.ctx = s.canvas.getContext('2d');
		}
		// end of checking

		//get new port List
		if (level_has_been_changed) {
			this.haveToInitPort = true;
		}

		//calculate new tile size
		if (level_has_been_changed || filter_has_been_changed || canvasSize_has_been_changed) {
			this.haveToCalculateTileSize = true;
			
		}

		//calculate group and order
		if (level_has_been_changed || groupBy_has_been_changed || filter_has_been_changed) {
			this.haveToCalculateGroupAndOrder = true;
			s.lookingIndex = -1;	//reset lookingIndex
		}

		//calulate level border
		if (level_has_been_changed || groupBy_has_been_changed || filter_has_been_changed || canvasSize_has_been_changed) {
			this.haveToCalculateLevelBorder = true;
		}

		//update color
		if (level_has_been_changed || timeMode_has_been_changed) {
			this.haveToUpdateColor = true;
			this.haveToUpdateIncident = true;
		}

		//trigger flag to draw new state
		this.haveToTriggerValidFlag = true;

		//clear to-do list
		this.adaptToChange()
	}

	this.adaptToChange = function () {
		if (!isAdapting) {
			isAdapting = true;
			if (this.haveToInitPort) {
				this.haveToInitPort = false;
				$("#section").mask("Loading initial data...");
				$.getJSON('http://203.146.64.37:8080/port/init/', { 'level': this.level }).done(
					function (json) {
						console.log("getInit");
						console.log(json);
						portlist = {};
						console.log(json.length);
						for (var i = 0; i < json.length; i++) {
							portlist[json[i]['oid']] = json[i]
						}
						isAdapting = false;
						s.option.adaptToChange();
					})
				.fail(function (jqxhr, textStatus, error) {
					var err = textStatus + ', ' + error;
					console.log("Request Failed: " + err);
					isAdapting = false;
				})
				.always(
					function () {
						//$("#section").unmask();
						$("#section").mask("Loading color...");
						isAdapting = false;
					}
				);
			}
			else if (this.haveToCalculateTileSize) {
				this.haveToCalculateTileSize = false;
				var total = 0;
				if (s.option.filter) {
					for (var oid in portlist) {
						if (portlist[oid]['inFilter'] == 1)
							total++;
					}
				}
				else {
					total = Object.keys(portlist).length;
				}

				total = Math.max(total, 1);

				var areaHeight = Math.max(this.canvasHeight - paddingTop - paddingBottom, 0);
				var areaWidth = Math.max(this.canvasWidth - paddingLeft - paddingRight, 0);
				var testingSize = Math.floor(Math.sqrt(areaHeight * areaWidth / total));
				while (testingSize > 0) {
					var maxHeight = Math.floor(areaHeight / testingSize);
					var maxColumn = Math.floor(Math.floor(areaWidth / testingSize) / blockPerColumn);
					var maxWidth = maxColumn * blockPerColumn;
					var maxCapacity = maxHeight * maxWidth;
					if (total <= maxCapacity)
						break;
					testingSize--;
				}
				if (testingSize > 0) {
					this.tileSize = testingSize;
					this.maxRow = maxHeight;

				}
				else
					console.error("There is not enough space to display all the tiles");

				isAdapting = false;
				this.adaptToChange();
			}
			else if (this.haveToCalculateGroupAndOrder) {
				this.haveToCalculateGroupAndOrder = false;

				//sort order
				s.order = [];

				for (var oid in portlist) {
					if (s.option.filter == false || (s.option.filter == true && portlist[oid]['inFilter'] == 1))
						s.order.push(parseInt(oid))
				}
				s.order.sort(function (a, b) {
					if (portlist[a]['level'] < portlist[b]['level'])
						return 1;
					else if (portlist[a]['level'] > portlist[b]['level'])
						return -1;
					else {
						if (portlist[a][s.option.groupBy] < portlist[b][s.option.groupBy])
							return -1;
						else if (portlist[a][s.option.groupBy] > portlist[b][s.option.groupBy])
							return 1;
						else {
							if (portlist[a]["inFilter"] < portlist[b]["inFilter"])
								return -1
							else if (portlist[a]["inFilter"] > portlist[b]["inFilter"])
								return 1;
							else
								return portlist[a]["Ifindex"] - portlist[b]["Ifindex"];
						}
					}

				});
				//clear indexing in portlist
				for (var oid in portlist) {
					portlist[oid]['index'] = null;
				}
				//backward indexing (map from oid to index)
				for (var i = 0; i < s.order.length; i++) {
					portlist[s.order[i]]['index'] = i;
				}

				//make list of group
				s.group = [];
				var currentGroup = { 'name': '~', 'start': -1, 'count': 0 }
				for (var i = 0; i < s.order.length; i++) {
					if (currentGroup['name'] != portlist[s.order[i]][this.groupBy]) {
						//store old group
						if (currentGroup['count'] > 0)
							s.group.push(currentGroup);
						//new group
						currentGroup = { 'name': portlist[s.order[i]][this.groupBy], 'start': i, 'count': 1 };
					}
					else {
						currentGroup['count']++;
					}
				}
				if (currentGroup['count'] > 0)
					s.group.push(currentGroup);

				isAdapting = false;
				this.adaptToChange();
			}
			else if (this.haveToCalculateLevelBorder) {
				this.haveToCalculateLevelBorder = false;
				if (this.level == "all") {
					//calculate levelBorder
					s.levelBorder = [[], [], [], []];
					//console.log(s.order.length + "xxx");
					for (var i = 0; i < s.order.length; i++) {
						var baseBlock = s.getPhysicalPosition(i);

						for (var j = 0; j < 4; j++) {
							var compareBlock = { 'row': baseBlock.row, 'column': baseBlock.column };
							if (j == 0) compareBlock.column--;
							else if (j == 1) compareBlock.row--;
							else if (j == 2) compareBlock.column++;
							else if (j == 3) compareBlock.row++;

							compareIndex = s.getTileIndexFromColumnRow(compareBlock.column, compareBlock.row);
							var baseLevel = portlist[s.order[i]]['level'];
							var compareLevel;
							if (compareIndex < 0 || compareIndex >= s.order.length)
								compareLevel = -1;
							else
								compareLevel = portlist[s.order[compareIndex]]['level'];

							if (baseLevel != compareLevel) {
								//console.log(i + "," + compareIndex + "=>" + baseLevel + "," + compareLevel);
								var basePoint = { 'x': paddingLeft + baseBlock.column * this.tileSize, 'y': paddingTop + baseBlock.row * this.tileSize };
								if (j == 0) {
									s.levelBorder[baseLevel].push({
										'fromx': basePoint.x,
										'fromy': basePoint.y,
										'tox': basePoint.x,
										'toy': basePoint.y + this.tileSize
									});
								}
								else if (j == 1) {
									s.levelBorder[baseLevel].push({
										'fromx': basePoint.x,
										'fromy': basePoint.y,
										'tox': basePoint.x + this.tileSize,
										'toy': basePoint.y
									});
								}
								else if (j == 2) {
									s.levelBorder[baseLevel].push({
										'fromx': basePoint.x + this.tileSize,
										'fromy': basePoint.y,
										'tox': basePoint.x + this.tileSize,
										'toy': basePoint.y + this.tileSize
									});
								}
								else if (j == 3) {
									s.levelBorder[baseLevel].push({
										'fromx': basePoint.x,
										'fromy': basePoint.y + this.tileSize,
										'tox': basePoint.x + this.tileSize,
										'toy': basePoint.y + this.tileSize
									});
								}
							}
						}
					}
				}

				isAdapting = false;
				this.adaptToChange();
			}
			else if (this.haveToUpdateColor) {
				s.option.lastUpdate = (Math.floor((new Date).getTime() / 1000));
				this.haveToUpdateColor = false;
				var inputDict = { 'level': this.level };
				if (s.option.timeMode == 1) {
					inputDict['timestampStart'] = this.selectedTime;
					inputDict['timestampEnd'] = this.selectedTime2;
				}
				console.log(inputDict);

				//$("#section").mask("Loading color...");
				$("#top_bar").mask("Loading color...");
				$.getJSON('http://203.146.64.37:8080/port/getColor/', inputDict).done(
					function (json) {
						console.log("getColor");
						console.log(json);
						//clear old color first
						for (var oid in portlist) {
							portlist[oid]['color'] = '#AAAAAA'; //'-';
						}
						//clear red link
						s.redLink = [];
						for (var i = 0; i < json.length; i++) {
							//console.log(json[i]['color']);
							if (json[i]['color'] == null || json[i]['color'].indexOf("#") != 0) {
								console.log(json[i]['color']);	//unusual case
								portlist[json[i]['oid']]['color'] = '#000000';
							}
							else {
								portlist[json[i]['oid']]['color'] = json[i]['color'];
							}
							//calculate new red link (just oid pairs are enough in order to make it flexible)
							var oid = json[i]['oid'];
							var colorCode = portlist[oid]['color'];
							if (colorCode[0] + colorCode[1] + colorCode[2] == '#FF'
								&& colorCode[5] + colorCode[6] == '00'
								&& colorCode[3] + colorCode[4] <= '80'     //'80'
								&& portlist[oid]['matched_oid'] != null && s.redLink.indexOf(portlist[oid]['matched_oid']) == -1) {
								s.redLink.push(oid);	//changed from [oid] ***
							}
						}

						//show last update time
						var ttt = new Date;
						$("#lastUpdateTime")[0].innerHTML = pad2(ttt.getHours()) + ":" + pad2(ttt.getMinutes());

						isAdapting = false;
						s.option.adaptToChange();
					}
				)
				.fail(
					function (jqxhr, textStatus, error) {
						var err = textStatus + ', ' + error;
						console.log("Request Failed: " + err);
					}
				)
				.always(
					function () {
						$("#top_bar").unmask();
						$("#section").unmask();
					}
				);
			}
			else if (this.haveToUpdateIncident) {
				this.haveToUpdateIncident = false;
				$.getJSON('http://203.146.64.37:8080/incident/getAll/').done(
					function (json) {
						console.log("getIncident");
						console.log(json);
						//replace incident 
						incident = json;

						gatherBlink();

						isAdapting = false;
						s.option.adaptToChange();
					}
				)
				.fail(
					function (jqxhr, textStatus, error) {
						var err = textStatus + ', ' + error;
						console.log("Request Failed: " + err);
					}
				)
				.always(
					function () {
						$("#top_bar").unmask();
						$("#section").unmask();
					}
				);
			}
			else if (this.haveToTriggerValidFlag) {
				//console.log("invalid");
				this.haveToTriggerValidFlag = false;
				s.valid = false;
				isAdapting = false;
			}
			else {
				isAdapting = false;
			}
		}
	}
}