$(document).ready(function() {
    // Sample data
    const actionsData = [
        { id: 1, name: "Follow Alert", screen: "Screen 1", duration: 5, points: 0, animation: false, picture: false, sound: false, video: false, description: 'Show Text "Thanks for following!"' },
        { id: 2, name: "Gift Alert", screen: "Screen 1", duration: 5, points: 0, animation: true, picture: false, sound: true, video: false, description: 'Show LEVEL_RAIN, Play Sound Falling Coins, Show Text "Thanks for {repeatcount}x {giftname}!"' },
        { id: 3, name: "Like Alert", screen: "Screen 1", duration: 5, points: 0, animation: true, picture: false, sound: false, video: false, description: 'Show LIKE_STORM, Show Text "Thanks for {totallikecount} Likes!"' },
        { id: 4, name: "Sub Alert", screen: "Screen 1", duration: 12, points: 0, animation: true, picture: false, sound: true, video: false, description: 'Show MAKE_IT_RAIN, Play Sound Notification Alert, Show Text "Thanks for subscribing!"' }
    ];

    const eventsData = [
        { id: 1, active: true, user: "Any", trigger: "Subscribe / Super Fan", actions: "Sub Alert" },
        { id: 2, active: true, user: "Any", trigger: "Tap 100+ Likes", actions: "Like Alert" },
        { id: 3, active: true, user: "Any", trigger: "Gift 1+ Coins", actions: "Gift Alert" },
        { id: 4, active: true, user: "Any", trigger: "Follow", actions: "Follow Alert" }
    ];

    const screensData = [
        { id: 1, name: "Screen 1", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=1", maxQueue: 5, status: "Ready" },
        { id: 2, name: "Screen 2", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=2", maxQueue: 5, status: "Offline" },
        { id: 3, name: "Screen 3", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=3", maxQueue: 5, status: "Offline" },
        { id: 4, name: "Screen 4", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=4", maxQueue: 5, status: "Offline" },
        { id: 5, name: "Screen 5", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=5", maxQueue: 5, status: "Offline" },
        { id: 6, name: "Screen 6", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=6", maxQueue: 5, status: "Offline" },
        { id: 7, name: "Screen 7", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=7", maxQueue: 5, status: "Offline" },
        { id: 8, name: "Screen 8", url: "https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen=8", maxQueue: 5, status: "Offline" }
    ];

    // Actions Enabled Checkbox
    $("#actionsEnabledCheckbox").dxCheckBox({
        text: "Enabled",
        value: true
    });

    // Actions DataGrid
    $("#onPageActionContainer").append(
        $("<div>").dxButton({
            text: "Create new Action",
            icon: "add",
            onClick: function() {
                alert("Create new action dialog would open here");
            }
        })
    );

    $("#onPageActionContainer").append(
        $("<div>").addClass("actionGrid").dxDataGrid({
            dataSource: actionsData,
            showBorders: true,
            searchPanel: { visible: true, placeholder: "Search existing actions..." },
            columns: [
                {
                    type: "buttons",
                    width: 130,
                    buttons: [
                        { hint: "Play", icon: "video", onClick: function(e) { alert("Play action: " + e.row.data.name); } },
                        { hint: "Edit", icon: "edit", onClick: function(e) { alert("Edit action: " + e.row.data.name); } },
                        { hint: "Duplicate", icon: "copy", onClick: function(e) { alert("Duplicate action: " + e.row.data.name); } },
                        { hint: "Delete", icon: "trash", onClick: function(e) { alert("Delete action: " + e.row.data.name); } }
                    ]
                },
                { dataField: "name", caption: "Name" },
                { dataField: "screen", caption: "Screen" },
                { dataField: "duration", caption: "Duration (sec.)" },
                { dataField: "points", caption: "Points +/-" },
                { dataField: "animation", caption: "Animation", dataType: "boolean" },
                { dataField: "picture", caption: "Picture", dataType: "boolean" },
                { dataField: "sound", caption: "Sound", dataType: "boolean" },
                { dataField: "video", caption: "Video", dataType: "boolean" },
                { dataField: "description", caption: "Description" }
            ]
        })
    );

    // Events DataGrid
    $("#onPageEventContainer").append(
        $("<div>").dxButton({
            text: "Create new Event",
            icon: "add",
            onClick: function() {
                alert("Create new event dialog would open here");
            }
        })
    );

    $("#onPageEventContainer").append(
        $("<div>").addClass("eventGrid").dxDataGrid({
            dataSource: eventsData,
            showBorders: true,
            searchPanel: { visible: true, placeholder: "Search existing events..." },
            columns: [
                {
                    type: "buttons",
                    width: 80,
                    buttons: [
                        { hint: "Edit", icon: "edit", onClick: function(e) { alert("Edit event"); } },
                        { hint: "Delete", icon: "trash", onClick: function(e) { alert("Delete event"); } }
                    ]
                },
                { dataField: "active", caption: "Active", dataType: "boolean" },
                { dataField: "user", caption: "User" },
                { dataField: "trigger", caption: "Trigger" },
                { dataField: "actions", caption: "Action(s)" }
            ]
        })
    );

    // Screens DataGrid
    $("#onPageScreenContainer").dxDataGrid({
        dataSource: screensData,
        showBorders: true,
        columns: [
            { dataField: "name", caption: "Screen Name" },
            { dataField: "url", caption: "Screen URL (widget for OBS or Live Studio)", cellTemplate: function(container, options) {
                $("<a>").attr("href", options.value).text(options.value).appendTo(container);
            }},
            { dataField: "maxQueue", caption: "Max. queue length", dataType: "number" },
            { dataField: "status", caption: "Status", cellTemplate: function(container, options) {
                const color = options.value === "Ready" ? "#66d164" : "#ff7a7a";
                $("<span>").css("color", color).text(options.value).appendTo(container);
            }}
        ]
    });

    // Timer DataGrid
    $("#onPageTimerContainer").append(
        $("<div>").dxButton({
            text: "Create new Timer",
            icon: "add",
            onClick: function() {
                alert("Create new timer dialog would open here");
            }
        })
    );

    $("#onPageTimerContainer").append(
        $("<div>").dxDataGrid({
            dataSource: [],
            showBorders: true,
            noDataText: "No Timers defined",
            columns: [
                { type: "buttons", width: 80 },
                { dataField: "active", caption: "Active", dataType: "boolean" },
                { dataField: "interval", caption: "Interval (minutes)" },
                { dataField: "action", caption: "Action to execute" }
            ]
        })
    );

    // Event Simulator
    const simulatorHtml = `
        <table>
            <tr>
                <td><div id="btnSimFollow"></div></td>
                <td><div id="btnSimShare"></div></td>
                <td><div id="btnSimSub"></div></td>
                <td><div id="btnSimLike"></div></td>
            </tr>
        </table>
        <table>
            <tr>
                <td><div id="selectSimGift"></div></td>
                <td><div id="btnSimGift"></div></td>
            </tr>
        </table>
    `;
    $("#simulatorButtons").html(simulatorHtml);

    $("#btnSimFollow").dxButton({ text: "Simulate Follow", width: 160, onClick: function() { alert("Simulating Follow"); } });
    $("#btnSimShare").dxButton({ text: "Simulate Share", width: 160, onClick: function() { alert("Simulating Share"); } });
    $("#btnSimSub").dxButton({ text: "Simulate Subscribe / Super Fan", width: 160, onClick: function() { alert("Simulating Subscribe"); } });
    $("#btnSimLike").dxButton({ text: "Simulate 15 Likes", width: 160, onClick: function() { alert("Simulating Likes"); } });
    $("#selectSimGift").dxSelectBox({ placeholder: "Select gift...", width: 487 });
    $("#btnSimGift").dxButton({ text: "Simulate Gift", width: 160, onClick: function() { alert("Simulating Gift"); } });
});
