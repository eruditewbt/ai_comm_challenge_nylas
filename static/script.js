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
  const manageEventLink = document.querySelector(".sidebar a[href='#manage-event']");

  manageBtn.addEventListener("click", () => {
    manageEventLink.click();
  });
});
