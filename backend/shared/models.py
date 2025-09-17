from django.db import models
from django.utils import timezone

class WorldBackground(models.Model):
    """
    Stores static world story background that can be reused across sessions.
    """
    content = models.TextField() # The static world background story

    def __str__(self):
        return f'WorldBackground: {self.content[:50]}...'

class Session(models.Model):
    """
    Stores a game session and its evolving world state.
    """
    world_background = models.ForeignKey(WorldBackground, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Session {self.id}'

class Turn(models.Model):
    """
    Core model: stores all data for a specific turn/year in the game.
    Uses (session, year) as composite unique key to support multiple parallel sessions.
    Each Turn has Django's auto-generated 'id' as primary key.
    """
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='turns')
    year = models.IntegerField() # Year within this session (e.g., 2035, 2036...)
    
    # Question phase data
    question = models.TextField(blank=True) # Generated question text
    question_generated_at = models.DateTimeField(null=True, blank=True)
    
    # User interaction (for shared session voting/consensus)
    user_choice = models.ForeignKey('Option', on_delete=models.SET_NULL, null=True, blank=True, related_name='chosen_by_turns') # Reference to the chosen option
    
    # Image management (preserved from teammate's design)
    displayed_image_rel = models.CharField(max_length=512, blank=True) # revealed image rel path for this turn/question

    class Meta:
        ordering = ['session', 'year']
        unique_together = ['session', 'year'] # Composite key: each (session, year) is unique

    def __str__(self):
        return f'Turn {self.year} (Session {self.session.id})'

class Option(models.Model):
    """
    Stores individual options for a specific turn.
    Each turn has exactly 2 options (A, B) with corresponding scenarios and image prompts.
    """
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE, related_name='options')
    
    # Option with label (A or B)
    label = models.CharField(max_length=1) # A, B
    option_text = models.TextField(blank=True) # The actual option text displayed to user (may be empty initially)
    
    # Image generation prompt
    image_text = models.TextField(blank=True) # LLM generated prompt for image generation (can be empty initially)

    # Scenario description
    scenario = models.TextField(blank=True) # Generated scenario description for this option (can be empty initially)
    
    # RAG and LLM interaction data
    scenario_query_text = models.TextField(blank=True) # Query text for generating next scenario based on this option (can be empty initially)
    question_query_text = models.TextField(blank=True) # Query text for generating next question based on this option (can be empty initially)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['label']
        unique_together = ['turn', 'label'] # Ensure one option per label per turn

    def __str__(self):
        return f'Option {self.label} for Turn {self.turn.year}'

class ImageRender(models.Model):
    """
    Records image generation attempts for a given option.
    """
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('ready', 'ready'),
        ('failed', 'failed'),
    ]
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='renders')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    image_rel = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Render {self.id} ({self.status}) for Option {self.option.label}'

class DefaultQueryList(models.Model):
    """
    Stores the initial query keywords list for year 2035 (when year-1 == 2034).
    """
    keyword = models.CharField(max_length=255)

    def __str__(self):
        return f'Default Query: {self.keyword}'
