"""
FastAPI Tests for High School Management System API

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and initial state
- Act: Execute the API call being tested
- Assert: Verify the response and side effects
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient connected to the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Fixture that resets the activities database before each test.
    This ensures tests are isolated and don't affect each other.
    """
    # Store original activities
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original activities after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


class TestRootEndpoint:
    """Tests for GET / (root redirect)"""
    
    def test_root_redirect(self, client):
        """
        Arrange: No setup needed
        Act: GET request to root path
        Assert: Should redirect to /static/index.html with 307 status
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "index.html" in response.headers.get("location", "")


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """
        Arrange: No setup needed
        Act: GET request to /activities
        Assert: Should return all activities with correct structure
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
    
    def test_activities_have_participants(self, client):
        """
        Arrange: No setup needed
        Act: GET request to /activities
        Assert: Each activity should include participants list
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name, activity_details in data.items():
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
    
    def test_activities_include_required_fields(self, client):
        """
        Arrange: No setup needed
        Act: GET request to /activities
        Assert: Each activity has all required fields
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        required_fields = {"description", "schedule", "max_participants", "participants"}
        data = response.json()
        for activity in data.values():
            assert required_fields.issubset(activity.keys())


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """
        Arrange: Valid activity name and new email
        Act: POST signup request
        Assert: Should return 200 and add participant to activity
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email in activities[activity]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """
        Arrange: Valid email but non-existent activity
        Act: POST signup request for invalid activity
        Assert: Should return 404 error
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, client):
        """
        Arrange: Valid activity and email already registered
        Act: POST signup request with duplicate email
        Assert: Should return 400 error
        """
        # Arrange
        activity = "Chess Club"
        email = activities[activity]["participants"][0]  # Get existing participant
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students_same_activity(self, client):
        """
        Arrange: Two different emails for same activity
        Act: POST signup requests for both students
        Assert: Both should succeed and both should appear in participants
        """
        # Arrange
        activity = "Programming Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in activities[activity]["participants"]
        assert email2 in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count + 2
    
    def test_signup_response_format(self, client):
        """
        Arrange: Valid signup data
        Act: POST signup request
        Assert: Response should include confirmation message
        """
        # Arrange
        email = "testuser@mergington.edu"
        activity = "Gym Class"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert activity in data["message"]
        assert email in data["message"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """
        Arrange: Valid activity and existing participant
        Act: DELETE unregister request
        Assert: Should return 200 and remove participant
        """
        # Arrange
        activity = "Chess Club"
        email = activities[activity]["participants"][0]  # Get existing participant
        initial_count = len(activities[activity]["participants"])
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count - 1
    
    def test_unregister_nonexistent_activity(self, client):
        """
        Arrange: Valid email but non-existent activity
        Act: DELETE unregister request for invalid activity
        Assert: Should return 404 error
        """
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_non_participant(self, client):
        """
        Arrange: Valid activity but email not in participants
        Act: DELETE unregister request for non-participant
        Assert: Should return 404 error
        """
        # Arrange
        activity = "Chess Club"
        email = "nonparticipant@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_multiple_times(self, client):
        """
        Arrange: One participant unregistered once, then attempt again
        Act: First DELETE unregister succeeds, second DELETE fails
        Assert: First should be 200, second should be 404
        """
        # Arrange
        activity = "Programming Class"
        email = activities[activity]["participants"][0]
        
        # Act (first unregister)
        response1 = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Act (second unregister - should fail)
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 404
        assert email not in activities[activity]["participants"]
    
    def test_unregister_response_format(self, client):
        """
        Arrange: Valid unregister data
        Act: DELETE unregister request
        Assert: Response should include confirmation message
        """
        # Arrange
        activity = "Art Club"
        email = activities[activity]["participants"][0]
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert activity in data["message"]
        assert email in data["message"]


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_unregister(self, client):
        """
        Arrange: Valid activity and new email
        Act: Signup, then unregister same student
        Assert: Both operations succeed, final state shows no participant
        """
        # Arrange
        activity = "Tennis"
        email = "integration@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert signup
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert unregister
        assert unregister_response.status_code == 200
        assert email not in activities[activity]["participants"]
    
    def test_signup_unregister_signup_again(self, client):
        """
        Arrange: Valid activity and email
        Act: Signup, unregister, signup again
        Assert: All three operations succeed
        """
        # Arrange
        activity = "Drama Club"
        email = "cycletest@mergington.edu"
        
        # Act - First signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Act - Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Act - Second signup (should succeed now)
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response3.status_code == 200
        assert email in activities[activity]["participants"]
