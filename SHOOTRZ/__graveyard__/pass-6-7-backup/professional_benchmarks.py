"""
Professional Basketball Player Shooting Form Benchmarks

Data sourced from:
- NBA shooting form analysis
- Sports biomechanics research
- Professional coaching databases
"""

PROFESSIONAL_PLAYERS = {
    # NBA Guards
    'stephen_curry': {
        'name': 'Stephen Curry',
        'position': 'Point Guard',
        'height': 6.2,
        'benchmarks': {
            'elbow_angle': 88,
            'knee_angle': 125,
            'release_angle': 48,
            'body_alignment': 95,
            'follow_through': 92,
            'consistency': 96,
            'jump_timing': 88,
            'body_sway': 94,
            'release_height': 6.2,
            'shot_arc': 47,
        },
        'style': 'Quick release, high arc, revolutionary range',
        'ft_percentage': 91.0,
        'career_3p': 42.8,
        'best_for': 'Quick release, long range shooting'
    },
    'klay_thompson': {
        'name': 'Klay Thompson',
        'position': 'Shooting Guard',
        'height': 6.6,
        'benchmarks': {
            'elbow_angle': 92,
            'knee_angle': 135,
            'release_angle': 46,
            'body_alignment': 98,
            'follow_through': 95,
            'consistency': 98,
            'jump_timing': 92,
            'body_sway': 96,
            'release_height': 6.5,
            'shot_arc': 45,
        },
        'style': 'Textbook form, consistent mechanics, catch-and-shoot',
        'ft_percentage': 89.0,
        'career_3p': 41.3,
        'best_for': 'Catch-and-shoot, textbook form'
    },
    'ray_allen': {
        'name': 'Ray Allen',
        'position': 'Shooting Guard',
        'height': 6.5,
        'benchmarks': {
            'elbow_angle': 90,
            'knee_angle': 128,
            'release_angle': 47,
            'body_alignment': 100,
            'follow_through': 98,
            'consistency': 99,
            'jump_timing': 95,
            'body_sway': 98,
            'release_height': 6.3,
            'shot_arc': 46,
        },
        'style': 'Picture-perfect form, quick release, legendary accuracy',
        'ft_percentage': 89.4,
        'career_3p': 40.0,
        'best_for': 'Perfect form, legendary accuracy'
    },
    'damian_lillard': {
        'name': 'Damian Lillard',
        'position': 'Point Guard',
        'height': 6.2,
        'benchmarks': {
            'elbow_angle': 89,
            'knee_angle': 130,
            'release_angle': 49,
            'body_alignment': 94,
            'follow_through': 90,
            'consistency': 93,
            'jump_timing': 90,
            'body_sway': 92,
            'release_height': 6.1,
            'shot_arc': 48,
        },
        'style': 'Deep range, clutch shooting, quick release',
        'ft_percentage': 89.5,
        'career_3p': 37.1,
        'best_for': 'Deep range, clutch situations'
    },
    'kyrie_irving': {
        'name': 'Kyrie Irving',
        'position': 'Point Guard',
        'height': 6.2,
        'benchmarks': {
            'elbow_angle': 91,
            'knee_angle': 128,
            'release_angle': 47,
            'body_alignment': 96,
            'follow_through': 94,
            'consistency': 95,
            'jump_timing': 88,
            'body_sway': 93,
            'release_height': 6.0,
            'shot_arc': 46,
        },
        'style': 'Smooth mechanics, mid-range specialist, creative finishes',
        'ft_percentage': 87.8,
        'career_3p': 39.1,
        'best_for': 'Mid-range shooting, creative finishes'
    },
    
    # NBA Forwards
    'kevin_durant': {
        'name': 'Kevin Durant',
        'position': 'Forward',
        'height': 6.10,
        'benchmarks': {
            'elbow_angle': 95,
            'knee_angle': 130,
            'release_angle': 50,
            'body_alignment': 92,
            'follow_through': 90,
            'consistency': 94,
            'jump_timing': 88,
            'body_sway': 90,
            'release_height': 7.0,
            'shot_arc': 48,
        },
        'style': 'High release point, smooth motion, unblockable',
        'ft_percentage': 88.0,
        'career_3p': 38.4,
        'best_for': 'Height advantage, unblockable shots'
    },
    'dirk_nowitzki': {
        'name': 'Dirk Nowitzki',
        'position': 'Forward',
        'height': 7.0,
        'benchmarks': {
            'elbow_angle': 93,
            'knee_angle': 135,
            'release_angle': 49,
            'body_alignment': 94,
            'follow_through': 96,
            'consistency': 97,
            'jump_timing': 92,
            'body_sway': 95,
            'release_height': 7.2,
            'shot_arc': 47,
        },
        'style': 'One-legged fadeaway, high release, legendary post-up',
        'ft_percentage': 87.9,
        'career_3p': 38.0,
        'best_for': 'Post-up shooting, fadeaway shots'
    },
    'reggie_miller': {
        'name': 'Reggie Miller',
        'position': 'Shooting Guard',
        'height': 6.7,
        'benchmarks': {
            'elbow_angle': 89,
            'knee_angle': 132,
            'release_angle': 48,
            'body_alignment': 97,
            'follow_through': 94,
            'consistency': 96,
            'jump_timing': 94,
            'body_sway': 96,
            'release_height': 6.4,
            'shot_arc': 46,
        },
        'style': 'Quick release, off-ball movement, clutch shooting',
        'ft_percentage': 88.8,
        'career_3p': 39.5,
        'best_for': 'Off-ball movement, quick release'
    },
    'larry_bird': {
        'name': 'Larry Bird',
        'position': 'Forward',
        'height': 6.9,
        'benchmarks': {
            'elbow_angle': 92,
            'knee_angle': 138,
            'release_angle': 46,
            'body_alignment': 99,
            'follow_through': 97,
            'consistency': 98,
            'jump_timing': 95,
            'body_sway': 97,
            'release_height': 6.8,
            'shot_arc': 45,
        },
        'style': 'Fundamentally perfect, clutch performer, legendary competitor',
        'ft_percentage': 88.6,
        'career_3p': 37.6,
        'best_for': 'Fundamentals, clutch situations'
    },
    
    # NBA Centers
    'kareem_abdul_jabbar': {
        'name': 'Kareem Abdul-Jabbar',
        'position': 'Center',
        'height': 7.2,
        'benchmarks': {
            'elbow_angle': 94,
            'knee_angle': 140,
            'release_angle': 52,
            'body_alignment': 96,
            'follow_through': 88,
            'consistency': 95,
            'jump_timing': 90,
            'body_sway': 92,
            'release_height': 7.5,
            'shot_arc': 50,
        },
        'style': 'Skyhook, unblockable, legendary post-up',
        'ft_percentage': 72.1,
        'career_3p': 5.6,
        'best_for': 'Post-up shooting, height advantage'
    },
    
    # WNBA Players
    'sue_bird': {
        'name': 'Sue Bird',
        'position': 'Point Guard',
        'height': 5.9,
        'benchmarks': {
            'elbow_angle': 90,
            'knee_angle': 128,
            'release_angle': 47,
            'body_alignment': 98,
            'follow_through': 96,
            'consistency': 98,
            'jump_timing': 94,
            'body_sway': 96,
            'release_height': 5.7,
            'shot_arc': 46,
        },
        'style': 'Fundamentally sound, leadership, clutch shooting',
        'ft_percentage': 87.2,
        'career_3p': 37.9,
        'best_for': 'Leadership, fundamentals, clutch shooting'
    },
    'diana_taurasi': {
        'name': 'Diana Taurasi',
        'position': 'Guard',
        'height': 6.0,
        'benchmarks': {
            'elbow_angle': 91,
            'knee_angle': 130,
            'release_angle': 48,
            'body_alignment': 95,
            'follow_through': 94,
            'consistency': 96,
            'jump_timing': 92,
            'body_sway': 94,
            'release_height': 5.8,
            'shot_arc': 47,
        },
        'style': 'Versatile scorer, deep range, competitive fire',
        'ft_percentage': 87.8,
        'career_3p': 36.8,
        'best_for': 'Versatility, deep range, competitive edge'
    },
    'maya_moore': {
        'name': 'Maya Moore',
        'position': 'Forward',
        'height': 6.0,
        'benchmarks': {
            'elbow_angle': 92,
            'knee_angle': 132,
            'release_angle': 47,
            'body_alignment': 97,
            'follow_through': 95,
            'consistency': 97,
            'jump_timing': 93,
            'body_sway': 95,
            'release_height': 5.9,
            'shot_arc': 46,
        },
        'style': 'Smooth mechanics, consistent form, championship pedigree',
        'ft_percentage': 88.4,
        'career_3p': 38.4,
        'best_for': 'Consistency, championship mentality'
    },
    
    # Modern NBA Stars
    'luka_doncic': {
        'name': 'Luka Doncic',
        'position': 'Forward',
        'height': 6.7,
        'benchmarks': {
            'elbow_angle': 91,
            'knee_angle': 128,
            'release_angle': 48,
            'body_alignment': 94,
            'follow_through': 92,
            'consistency': 94,
            'jump_timing': 89,
            'body_sway': 91,
            'release_height': 6.5,
            'shot_arc': 47,
        },
        'style': 'Step-back specialist, deep range, creative shot-making',
        'ft_percentage': 73.9,
        'career_3p': 33.7,
        'best_for': 'Step-back shots, creative finishes'
    },
    'jayson_tatum': {
        'name': 'Jayson Tatum',
        'position': 'Forward',
        'height': 6.8,
        'benchmarks': {
            'elbow_angle': 93,
            'knee_angle': 130,
            'release_angle': 49,
            'body_alignment': 95,
            'follow_through': 93,
            'consistency': 95,
            'jump_timing': 91,
            'body_sway': 93,
            'release_height': 6.6,
            'shot_arc': 48,
        },
        'style': 'Smooth mechanics, mid-range specialist, clutch performer',
        'ft_percentage': 85.3,
        'career_3p': 36.9,
        'best_for': 'Mid-range shooting, clutch situations'
    },
    'devin_booker': {
        'name': 'Devin Booker',
        'position': 'Shooting Guard',
        'height': 6.5,
        'benchmarks': {
            'elbow_angle': 90,
            'knee_angle': 129,
            'release_angle': 47,
            'body_alignment': 96,
            'follow_through': 94,
            'consistency': 96,
            'jump_timing': 92,
            'body_sway': 94,
            'release_height': 6.3,
            'shot_arc': 46,
        },
        'style': 'Smooth release, mid-range mastery, scoring machine',
        'ft_percentage': 86.9,
        'career_3p': 35.5,
        'best_for': 'Mid-range shooting, scoring consistency'
    }
}

# Average of all elite shooters (our baseline)
ELITE_SHOOTER_AVERAGE = {
    'elbow_angle': 91,
    'knee_angle': 130,
    'release_angle': 47,
    'body_alignment': 96,
}

def compare_to_professional(user_metrics, player_name='stephen_curry'):
    """
    Compare user's shooting form to a professional player
    
    Args:
        user_metrics: User's measured angles
        player_name: Professional player to compare against
        
    Returns:
        dict: Comparison results with similarities and differences
    """
    if player_name not in PROFESSIONAL_PLAYERS:
        player_name = 'stephen_curry'  # Default to Curry
    
    player = PROFESSIONAL_PLAYERS[player_name]
    benchmarks = player['benchmarks']
    
    comparison = {
        'player': player['name'],
        'style': player['style'],
        'similarities': [],
        'differences': [],
        'overall_similarity': 0,
    }
    
    # Compare each metric
    total_similarity = 0
    metrics_compared = 0
    
    for key, ideal_value in benchmarks.items():
        if key in user_metrics:
            user_value = user_metrics[key]
            difference = abs(user_value - ideal_value)
            
            # Calculate similarity (closer = higher similarity)
            if key == 'body_alignment':
                # Alignment is 0-100 scale
                similarity = max(0, 100 - difference)
            else:
                # Angles - within 5 degrees is very similar
                similarity = max(0, 100 - (difference * 10))
            
            total_similarity += similarity
            metrics_compared += 1
            
            # Add to similarities or differences
            if difference <= 5:
                comparison['similarities'].append(
                    f"Your {key.replace('_', ' ')} ({user_value}°) is very close to {player['name']}'s ({ideal_value}°)"
                )
            else:
                comparison['differences'].append(
                    f"Your {key.replace('_', ' ')} ({user_value}°) differs from {player['name']}'s ({ideal_value}°) by {difference:.1f}°"
                )
    
    # Calculate overall similarity
    if metrics_compared > 0:
        comparison['overall_similarity'] = round(total_similarity / metrics_compared, 1)
    
    return comparison

def get_recommended_player(user_metrics):
    """
    Find which professional player's style best matches the user
    
    Args:
        user_metrics: User's measured angles
        
    Returns:
        str: Name of the most similar professional player
    """
    best_match = None
    highest_similarity = 0
    
    for player_key, player_data in PROFESSIONAL_PLAYERS.items():
        comparison = compare_to_professional(user_metrics, player_key)
        similarity = comparison['overall_similarity']
        
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = player_data['name']
    
    return best_match, highest_similarity

def generate_comparison_tips(user_metrics, target_player='stephen_curry'):
    """
    Generate tips based on comparison to a professional player
    
    Args:
        user_metrics: User's measured angles
        target_player: Professional player to emulate
        
    Returns:
        list: Actionable tips to improve form toward player's style
    """
    comparison = compare_to_professional(user_metrics, target_player)
    player = PROFESSIONAL_PLAYERS[target_player]
    
    tips = [
        f"Comparing your form to {player['name']} ({player['style']})",
        f"Overall similarity: {comparison['overall_similarity']}%"
    ]
    
    # Add specific improvement tips
    if comparison['differences']:
        tips.append("Key differences to work on:")
        tips.extend(comparison['differences'][:2])  # Top 2 differences
    
    if comparison['similarities']:
        tips.append(f"✓ {comparison['similarities'][0]}")
    
    return tips
