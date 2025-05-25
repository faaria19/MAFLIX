const backendUrl = "http://127.0.0.1:5000";
let currentIndexes = [];
let feedback = {};

document.addEventListener("DOMContentLoaded", () => {
    displayTopMovies();
    populateGenres();
});

function populateGenres() {
    const genres = [
        "Action", "Adventure", "Animation", "Biography", "Comedy",
        "Crime", "Drama", "Fantasy", "Horror", "Mystery", "Romance",
        "Sci-Fi", "Thriller", "War", "Western"
    ];
    const select = document.getElementById("genreSelect");
    genres.forEach(g => {
        const option = document.createElement("option");
        option.value = g;
        option.textContent = g;
        select.appendChild(option);
    });
}

function displayTopMovies() {
    const topMovies = [
  {
    title: "The Shawshank Redemption",
    imdb: "https://www.imdb.com/title/tt0111161/",
    poster: "/static/img/shawshank.jpg",
    rating: "9.3"
  },
  {
    title: "The Godfather",
    imdb: "https://www.imdb.com/title/tt0068646/",
    poster: "/static/img/god-father.jpg",
    rating: "9.2"
  },
  {
    title: "The Dark Knight",
    imdb: "https://www.imdb.com/title/tt0468569/",
    poster: "/static/img/dark-knight.jpg",
    rating: "9.0"
  },
  {
    title: "Fight Club",
    imdb: "https://www.imdb.com/title/tt0137523/",
    poster: "/static/img/fight-club.jpg",
    rating: "8.8"
  },
  {
    title: "Inception",
    imdb: "https://www.imdb.com/title/tt1375666/",
    poster: "/static/img/inception.jpg",
    rating: "8.8"
  }
];
    displayMovies(topMovies);
}

function displayMovies(movies) {
    const container = document.getElementById("movies-container");
    container.innerHTML = "";
    movies.forEach((movie, idx) => {
        const card = document.createElement("div");
        card.className = "movie-card";
        card.innerHTML = `
      <img src="${movie.poster}" alt="${movie.title}" />
      <h3><a href="${movie.imdb || '#'}" target="_blank">${movie.title}</a></h3>
      <p>⭐ ${movie.rating || movie.vote_average}</p>
      ${movie.genres ? `<p><b>${movie.genres}</b></p>` : ""}
      ${movie.index !== undefined ? `
        <button onclick="sendFeedback(${movie.index}, 'relevant')">👍</button>
        <button onclick="sendFeedback(${movie.index}, 'not_relevant')">👎</button>
      ` : ""}
    `;
        container.appendChild(card);
    });
}

function getRecommendations() {
    const movieName = document.getElementById("movieInput").value;
    const genre = document.getElementById("genreSelect").value;

    fetch(`${backendUrl}/recommend`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            movieName,
            genre,
            feedback,
            currentRecIndexes: currentIndexes
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.recommendations) {
                currentIndexes = data.recommendations.map(r => r.index);
                feedback = {};
                displayMovies(data.recommendations);
                showEvaluation(data.evaluation);
            } else {
                alert("No recommendations found.");
            }
        });
}

function sendFeedback(index, type) {
    feedback[index] = type;
    getRecommendations();
}

function showEvaluation(evaluation) {
    const evalDiv = document.getElementById("evaluation");
    if (!evaluation || evaluation.precision === null) {
        evalDiv.textContent = "";
        return;
    }
    evalDiv.innerHTML = `
    <p><strong>Evaluation:</strong></p>
    <ul>
      <li>✅ Relevant: ${evaluation.relevant_feedback_count}</li>
      <li>❌ Not Relevant: ${evaluation.not_relevant_feedback_count}</li>
      <li>🎯 Precision: ${evaluation.precision}</li>
    </ul>
  `;
}
