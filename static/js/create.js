$(document).ready(function () {    
    const url = $(location).attr('pathname');
    if (url.startsWith("/")) {
        populate();
    }
    if (url.startsWith("/view")) {
        seeStory();
        console.log("pinged")
    }
    if (window.location.pathname.includes('/edit')) {
        seePrev();
        document.getElementById('save').value = "Save edits";
        document.getElementById('discard').innerHTML = '&nbsp;&nbsp;<button type="button" class="btn btn-danger" id="discardButton">Discard Changes</button>';
    }
    if (window.location.pathname.includes('/create') || window.location.pathname.includes('/edit') || window.location.pathname.includes('/submission')) {
        document.getElementById('adventure').addEventListener('submit', function(event) {
            event.preventDefault();
            if (window.location.pathname.includes('/edit')) {
                const pathParts = window.location.pathname.split('/');
                let id = pathParts[pathParts.length - 1];
                const confirmed = confirm("Are you sure you want to continue?");
                if (confirmed) {
                    edited = submitForm();
                    if (edited) {
                        editStory(edited, id);
                    } else {
                        return;
                    }
                } else {
                    return;
                }
            }
            result = submitForm();
            if (result) {
                submitStory(result);
            } else {
                return;
            }
        });   
        document.getElementById('discardButton').addEventListener('click', function() {
            const pathParts = window.location.pathname.split('/');
            let id = pathParts[pathParts.length - 1];
            const confirmed = confirm("Are you sure you want to discard all changes?");
            if (confirmed) {
                window.location.href = "/view/" + id;
            } else {
                return;
            }
        });
    }
});


function submitStory(newStory) {
    $.ajax({
        type: "POST",
        url: "/create/submit",
        contentType: "application/json",
        data: JSON.stringify(newStory),
        success: function(response) {
            id = response.id;
            statusAppend(id);
        },
        error: function(request, status, error) {
            alert('We could not submit your story. Please try again!');
        }
    })
}

function editStory(edited, id) {
    $.ajax({
        type: "POST",
        url: "/edit/" + id,
        contentType: "application/json",
        data: JSON.stringify(edited),
        success: function(response) {
            window.location.href = "/view/" + id;
        },
        error: function(request, status, error) {
            alert('We could not submit your story. Please try again!');
        }
    })
}

function statusAppend(id) {
    document.getElementById("successStatus")
        .innerHTML +=
        `<div id="successMessage">
            <span class="dark_grey">New story successfully created.</span>
            <a href="/view/${id}" style="font-size: 30px;">See it here!</a>
            <br><br>
        </div>`;
}

function submitForm() {
    console.log("pressed")
    let isValid = true;
    document.getElementById('name_error').value = '';
    for (let i = 1; i <= 12; i++) {
        document.getElementById(`${i}_error`).innerHTML = '';
    }
    const name = document.getElementById('name').value.trim();
    if (name === '') {
        document.getElementById('name_error').innerHTML = `<span style="color: red;">The name field cannot be empty.</span>`;
        isValid = false;
    }
    for (let i = 1; i <= 12; i++) {
        const input = document.getElementById(`stage_${i}`).value.trim();
        if (input === '') {
            document.getElementById(`${i}_error`).innerHTML = `<span style="color: red;">This stage cannot be empty.</span>`;
            isValid = false;
        }
    }
    if (isValid) {
        let newStory = {
            name: name,
            stage_1: document.getElementById('stage_1').value,
            stage_2: document.getElementById('stage_2').value,
            stage_3: document.getElementById('stage_3').value,
            stage_4: document.getElementById('stage_4').value,
            stage_5: document.getElementById('stage_5').value,
            stage_6: document.getElementById('stage_6').value,
            stage_7: document.getElementById('stage_7').value,
            stage_8: document.getElementById('stage_8').value,
            stage_9: document.getElementById('stage_9').value,
            stage_10: document.getElementById('stage_10').value,
            stage_11: document.getElementById('stage_11').value,
            stage_12: document.getElementById('stage_12').value
        }
        clearForm();
        $('#name').focus();
        return newStory;
    }
    if (!isValid) {
        return;
    }
}
function seePrev() {
    const story = stories[current_id];
    for (let i = 1; i <= 12; i++) {
        document.getElementById(`stage_${i}`).value = story[`stage_${i}`];
    }
}

function clearForm() {
    document.getElementById('name').value = '';
    document.getElementById('name_error').value = '';
    for (let i = 1; i <= 12; i++) {
        document.getElementById(`stage_${i}`).value = '';
        document.getElementById(`${i}_error`).innerHTML = '';
    }
}

function populate() {
    $("#story_container").empty();
    Object.entries(stories).forEach(([id, story]) => {
        const storyCard = $(`
            <div class="story-card">
                <h3>${story.name}</h3>
                <p>${story.stage_1.slice(0, 100)}...</p>
                <div class="story-buttons">
                    <a href="/view/${id}" class="btn-small">View</a>
                </div>
            </div>
        `);
        $("#story_container").append(storyCard);
    });
}

function seeStory() {
    $("#storage").append(`<h2 class="text-center mb-4">${story.name}</h2><br>`);
    for (let i = 1; i <= 12; i++) {
        stage_name = all_stage_data[i]["name"];
        stage_description = all_stage_data[i]["description"]
        $("#storage").append(`
            <div class="mb-3">
                <h3>${stage_name}</h4><br>
                <h4>${stage_description}</h3><br>
                <p>${story[`stage_${i}`]}</p><br>
            </div>
        `);
    }
}

function statusAppend(id) {
    document.getElementById("successStatus")
        .innerHTML +=
        `<div id="successMessage">
            <span class="dark_grey">New story successfully created.</span>
            <a href="/view/${id}">See it here!</a>
            <br><br>
        </div>`;
}