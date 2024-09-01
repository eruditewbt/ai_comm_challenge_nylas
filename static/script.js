document.addEventListener("DOMContentLoaded", () => {
  const days = document.querySelectorAll(".day");
  days.forEach((day) => {
    day.addEventListener("click", () => {
      alert(`You clicked on day ${day.textContent}`);
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.querySelector(".sidebar ul li span");
  const sidebar = document.querySelector(".sidebar");
  const navLinks = document.querySelectorAll(".sidebar ul li a");

  toggleButton.addEventListener("click", function () {
    sidebar.classList.toggle("collapsed");

    document.body.classList.toggle("dark-mode");

    if (sidebar.classList.contains("collapsed")) {
      toggleButton.innerHTML = '<i class="fas fa-toggle-off"></i>';
    } else {
      toggleButton.innerHTML = '<i class="fas fa-toggle-on"></i>';
    }

    navLinks.forEach((link) => {
      if (sidebar.classList.contains("collapsed")) {
        link.style.opacity = "0";
      } else {
        link.style.opacity = "1";
      }
    });
  });
});

function initializeSidebar() {
  const icons = document.querySelectorAll(".sidebar i");
  const navLinks = document.querySelectorAll(".sidebar ul li a");

  // Convert NodeList to array and slice from the second element
  Array.from(icons)
    .slice(1)
    .forEach((icon, index) => {
      icon.addEventListener("click", () => {
        navLinks[index + 1].click(); // Adjust the index to match the original array
      });
    });
}

// Call the function to initialize the sidebar
initializeSidebar();

function openTab(evt, tabName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

document.addEventListener("DOMContentLoaded", () => {
  const events = [
    // Example event data
    {
      title: "Event 1",
      description: "Description 1",
      location: "Location 1",
      category: "meeting",
      start: "2023-10-01T10:00",
      end: "2023-10-01T12:00",
    },
    {
      title: "Event 2",
      description: "Description 2",
      location: "Location 2",
      category: "workshop",
      start: "2023-10-02T10:00",
      end: "2023-10-02T12:00",
    },
    // Add more events as needed
  ];

  function checkNotifications() {
    const now = new Date();
    const notificationList = document.getElementById("notification-list");
    notificationList.innerHTML = "";

    events.forEach((event) => {
      const eventStart = new Date(event.start);
      const timeDiff = eventStart - now;
      const minutesDiff = Math.floor(timeDiff / 60000);

      if (minutesDiff > 0 && minutesDiff <= 30) {
        const li = document.createElement("li");
        li.textContent = `Upcoming Event: ${event.title} at ${event.start}`;
        notificationList.appendChild(li);
      }
    });
  }

  // Check for notifications every minute
  setInterval(checkNotifications, 60000);

  // Initial check
  checkNotifications();
});

document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll(".sidebar a");
  const navIcons = document.querySelectorAll(".sidebar i");
  const sections = document.querySelectorAll(".main-content");

  function showSection(hash) {
    sections.forEach((section) => {
      if (section.id === hash) {
        section.style.display = "block";
      } else {
        section.style.display = "none";
      }
    });
  }

  function updateIconColor(clickedLink) {
    navLinks.forEach((navLink, index) => {
      if (navLink == clickedLink) {
        navIcons[index].style.color = "var(--accent-color)"; // Set color of the clicked icon
      } else {
        navIcons[index].style.color = "var(--secondary-color)"; // Reset color of all icons
      }
    });
  }

  navLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const hash = link.getAttribute("href").substring(1);
      showSection(hash);
      updateIconColor(link);
    });
  });

  // Show the default section (home) on page load
  showSection("home");
  // Set the default icon color on page load
  const defaultLink = document.querySelector(".sidebar a[href='#home']");
  if (defaultLink) {
    updateIconColor(defaultLink);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const manageBtn = document.getElementById("manage_btn");
  const manageEventLink = document.querySelector(
    ".sidebar a[href='#manage-event']"
  );

  manageBtn.addEventListener("click", () => {
    manageEventLink.click();
  });
});

//create event
document
  .getElementById("ai_create_event_btn")
  .addEventListener("click", async function () {
    const eventText = document.getElementById("ai_event_text").value;
    const resultElement = document.querySelector(".ai-result");

    if (!eventText) {
      alert("Please enter event details.");
      return;
    }

    try {
      const response = await fetch("/create-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "AI Generated Event", // Placeholder title
          location: "AI Generated Location", // Placeholder location
          description: eventText,
          start_time: new Date().toISOString(), // Placeholder start time
          end_time: new Date(
            new Date().getTime() + 60 * 60 * 1000
          ).toISOString(), // Placeholder end time (1 hour later)
        }),
      });

      const result = await response.json();

      if (result.status === "success") {
        resultElement.innerHTML = "Event created successfully!";
        // Optionally, you can update the UI with the new event details
      } else {
        resultElement.innerHTML = "Error creating event: " + result.body;
      }
    } catch (error) {
      console.error("Error:", error);
      resultElement.innerHTML = "An error occurred while creating the event.";
    }
  });

document
  .getElementById("event-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault(); // Prevent the default form submission

    const form = event.target;
    const formData = new FormData(form);
    const formResult = document.querySelector(".form-result");

    const data = {
      title: formData.get("title"),
      description: formData.get("description"),
      location: formData.get("location"),
      start_time: new Date(formData.get("start")).toISOString(),
      end_time: new Date(formData.get("end")).toISOString(),
    };

    try {
      const response = await fetch("/create-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      if (result.status === "success") {
        formResult.innerHTML = "Event created successfully!";
        // Optionally, you can update the UI with the new event details
      } else {
        formResult.innerHTML = "Error creating event: " + result.body;
      }
    } catch (error) {
      console.error("Error:", error);
      formResult.innerHTML = "An error occurred while creating the event.";
    }
  });
  
// form submission upload file
document.querySelector("form").addEventListener("submit", async (event) => {
  event.preventDefault(); // Prevent the default form submission

  const form = event.target;
  const formData = new FormData(form);
  const formResult = document.querySelector(".form-result");

  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: formData,
    });

    const result = await response.json();
    if (response.ok) {
      formResult.innerHTML = `
        <div class="alert alert-success">
          File uploaded successfully!<br>
          Filename: ${result.filename}<br>
          Username: ${result.username}<br>
        </div>`;
    } else {
      formResult.innerHTML = `
        <div class="alert alert-danger">
          Error uploading file: ${result.message}
        </div>`;
    }
  } catch (error) {
    console.error("Error:", error);
    formResult.innerHTML = `
      <div class="alert alert-danger">
        An error occurred while uploading the file.
      </div>`;
  }
});

//fetch data
document.addEventListener("DOMContentLoaded", () => {
  async function fetchLatestData() {
    try {
      const response = await fetch("/latest-data");
      const data = await response.json();

      if (data.error) {
        console.error("Error fetching latest data:", data.error);
        return;
      }

      // Update profile picture and username
      document.querySelector(".profile img").src = data.profile_url;
      document.querySelector(".profile span").textContent = data.username;

      // Update event statistics
      document.querySelector(
        "#all p"
      ).textContent = `all: ${data.events.length}`;
      document.querySelector(
        "#current p"
      ).textContent = `current events: ${data.current_events.length}`;
      document.querySelector(
        "#upcoming p"
      ).textContent = `upcoming events: ${data.upcoming_events.length}`;
      document.querySelector(
        "#completed p"
      ).textContent = `completed events: ${data.completed_events.length}`;

      // Update event lists
      updateEventList("#all ul", data.events);
      updateEventList("#current ul", data.current_events);
      updateEventList("#upcoming ul", data.upcoming_events);
      updateEventList("#completed ul", data.completed_events);

      // Update summary
      document.querySelector(".quote p").textContent = data.summary;

      // Update messages
      updateMessageList(".messages .list-group", data.messages);

      // Update date
      document.querySelector(".calendar h3").textContent = data.date;
    } catch (error) {
      console.error("Error fetching latest data:", error);
    }
  }

  function updateEventList(selector, events) {
    const list = document.querySelector(selector);
    list.innerHTML = "";
    events.forEach((event) => {
      const listItem = document.createElement("li");
      listItem.className = "list-group-item";
      listItem.textContent = event;
      list.appendChild(listItem);
    });
  }

  function updateMessageList(selector, messages) {
    const list = document.querySelector(selector);
    list.innerHTML = "";
    messages.forEach((message) => {
      const listItem = document.createElement("li");
      listItem.className = "list-group-item";
      const messageDiv = document.createElement("div");
      messageDiv.className = "message";
      const img = document.createElement("img");
      img.src = message.profile_url;
      img.alt = "Profile Picture";
      const contentDiv = document.createElement("div");
      contentDiv.className = "content";
      const name = document.createElement("h3");
      name.textContent = message.name;
      const content = document.createElement("p");
      content.textContent = message.content;
      contentDiv.appendChild(name);
      contentDiv.appendChild(content);
      messageDiv.appendChild(img);
      messageDiv.appendChild(contentDiv);
      listItem.appendChild(messageDiv);
      list.appendChild(listItem);
    });
  }

  // Fetch data every 5 seconds
  setInterval(fetchLatestData, 5000);

  // Initial fetch
  fetchLatestData();
});
