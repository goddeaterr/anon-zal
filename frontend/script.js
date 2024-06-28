document.addEventListener('DOMContentLoaded', () => {
    loadPosts();
    loadStats();
});

function getAnonName() {
    let anonName = localStorage.getItem('anonName');
    if (!anonName) {
        anonName = `Anon ${Math.floor(Math.random() * 1000)}`;
        localStorage.setItem('anonName', anonName);
    }
    return anonName;
}

function loadPosts() {
    fetch('/posts')
        .then(response => response.json())
        .then(posts => {
            const postsDiv = document.getElementById('posts');
            postsDiv.innerHTML = '';
            posts.forEach(post => {
                const isModerator = post.anon_name.includes('fa-user-shield');
                const postDiv = document.createElement('div');
                postDiv.className = 'post';
                postDiv.innerHTML = `
                    <p><strong>${post.anon_name}:</strong> ${post.content}</p>
                    <div class="actions">
                        <div>
                            <button onclick="likePost(${post.id})"><i class="fas fa-thumbs-up"></i> ${post.likes}</button>
                            <button onclick="dislikePost(${post.id})"><i class="fas fa-thumbs-down"></i> ${post.dislikes}</button>
                        </div>
                        <button onclick="toggleComments('${post.uuid}')"><i class="fas fa-comments"></i> Comments (${post.comments})</button>
                        ${isModerator ? `<button onclick="deletePost(${post.id})"><i class="fas fa-trash"></i> Delete</button>` : ''}
                    </div>
                    <div id="comments-${post.uuid}" class="comments" style="display: none;">
                        <textarea id="commentContent-${post.uuid}" placeholder="Add a comment"></textarea>
                        <button onclick="addComment('${post.uuid}')">Comment</button>
                        <div id="comments-list-${post.uuid}"></div>
                    </div>
                `;
                postsDiv.appendChild(postDiv);
            });
        });
}

function createPost() {
    const content = document.getElementById('postContent').value;
    if (content.trim()) {
        fetch('/posts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ anon_name: getAnonName(), content })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('postContent').value = '';
            loadPosts();
            loadStats();  // Update stats after creating a post
        });
    }
}

function likePost(postId) {
    fetch(`/posts/${postId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Anon-Name': getAnonName()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message !== 'Already liked') {
            loadPosts();
        }
    });
}

function dislikePost(postId) {
    fetch(`/posts/${postId}/dislike`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Anon-Name': getAnonName()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message !== 'Already disliked') {
            loadPosts();
        }
    });
}

function deletePost(postId) {
    fetch(`/posts/${postId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(() => {
        loadPosts();
    });
}

function deleteComment(commentId, postUuid) {
    fetch(`/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(() => {
        loadComments(postUuid);
        loadPosts();  // Update comments count
    });
}

function toggleComments(postUuid) {
    const commentsDiv = document.getElementById(`comments-${postUuid}`);
    if (commentsDiv.style.display === 'none') {
        commentsDiv.style.display = 'block';
        loadComments(postUuid);
    } else {
        commentsDiv.style.display = 'none';
    }
}

function loadComments(postUuid) {
    fetch(`/posts/${postUuid}/comments`)
        .then(response => response.json())
        .then(comments => {
            const commentsList = document.getElementById(`comments-list-${postUuid}`);
            commentsList.innerHTML = '';
            comments.forEach(comment => {
                const isModerator = comment.anon_name.includes('fa-user-shield');
                const commentDiv = document.createElement('div');
                commentDiv.className = 'comment';
                commentDiv.innerHTML = `<p><strong>${comment.anon_name}:</strong> ${comment.content}</p>
                ${isModerator ? `<button onclick="deleteComment(${comment.id}, '${postUuid}')"><i class="fas fa-trash"></i> Delete</button>` : ''}`;
                commentsList.appendChild(commentDiv);
            });
        });
}

function addComment(postUuid) {
    const content = document.getElementById(`commentContent-${postUuid}`).value;
    if (content.trim()) {
        fetch(`/posts/${postUuid}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ anon_name: getAnonName(), content })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById(`commentContent-${postUuid}`).value = '';
            loadComments(postUuid);
            loadPosts(); // Update comments count
        });
    }
}

function loadStats() {
    fetch('/stats')
        .then(response => response.json())
        .then(stats => {
            document.getElementById('totalVisitors').textContent = stats.total_visitors;
            document.getElementById('totalPosts').textContent = stats.total_posts;
        });
}
